import csv

from icp_with_alignment import icp_scaled_and_aligned
import sys
import argparse
import open3d as o3d
import numpy as np
from time import time
import pandas as pd
from viewer import point_cloud_viewer
from cloud_management import outliers_filter_v2, duplicates_filter_v2


def save_to_file(result, start_row, end_row, output_dir, thresh):
    frame = pd.DataFrame(result,
                         columns=["nube1", "tamaño_nube1", "nube2", "tamaño_nube2", "matcheos", "overlap", "label",
                                  "rmse", "radio", "giros"])
    path = output_dir + "/180_thresh_0.7_radio_" + str(thresh) + '_rows_' + str(start_row) + '_' + str(end_row) + ".csv"
    print(f'partial saving in {path}')
    frame.to_csv(path)

def main():
    input_dir =  '/data/mejores_no_espejadas_180/'
    output_dir = '/data/output/mejores_no_espejadas_180/' # '/data/output/180_v5/'#
    inputs_path = input_dir + "labels.csv"
    inputs_df = pd.read_csv(inputs_path)
    clouds = {}
    master = open(input_dir + 'master.csv')
    master_reader = csv.reader(master)
    start_row = 0 # numbered from1
    end_row = 125000 # 496505
    threshold_percentage_list = [0.1]   # porcentaje de la distancia en la nube a usar como trheshold
    save_interval = 100

    for name, label in zip(inputs_df["cloud_name"], inputs_df["label"]):
        cloud = o3d.io.read_point_cloud(input_dir + name)
        clouds[name] = cloud

    ##### hiper-parámetros ####
    n_neighbors = 1                     # cantidad de vecinos por cada punto de una nube con los que va a intentar alinear
    step = 1/4                          # paso de rotación de la nube "source_cloud" alrededor del eje z
    giros = 2 / step
    start_time = time()
    angle = np.pi * step

    clouds = outliers_filter_v2(clouds)
    clouds = outliers_filter_v2(clouds)
    clouds = outliers_filter_v2(clouds)
    clouds = outliers_filter_v2(clouds)
    clouds = outliers_filter_v2(clouds)
    clouds = outliers_filter_v2(clouds)
    clouds = duplicates_filter_v2(clouds)

    for thresh_idx, thresh in enumerate(threshold_percentage_list):
        result = np.empty((save_interval, 10), dtype=object)
        counter = 0
        local_counter = 0
        stime = time()
        overlap = 0
        lista = []
        try:
            next(master_reader, None)
            for i in range(start_row):
                next(master_reader, None)
            for i in range(end_row - start_row + 1):
                row = next(master_reader, None)
                if row is None:
                    break
                else:
                    cn1, label_1, cn2, label_2 = row[1:]
                    source = clouds[cn1]
                    target = clouds[cn2]
                    label = label_1 == label_2
                    start = time()

                    # for debug: comentar metric = icp_scale_and_aligned... y ver si corre hasta el final
                    # descomentar la siguiente línea
                    metric = icp_scaled_and_aligned(source, target, thresh, n_neighbors, angle, distance_criterion='mean')
                    # metric = [1, 1, 1, 0, 0, 0]

                    result[local_counter, :] = cn1, metric[1], cn2, metric[2], metric[0], overlap, label, metric[
                            3], thresh, giros

                    # Devuelve: (cantidad de matcheos, cantidad de puntos nube source_cloud, cantidad de puntos nube target_cloud,
                    # rmse, conjunto de correspondencia)

                    end_t = time()

                    print(f"thresh: {thresh} ; thresh {thresh_idx + 1} de {len(threshold_percentage_list)}")
                    print(f'{cn1} (n:{metric[1]})', cn2 + f' (n:{metric[2]})')
                    print(f'matcheos: {metric[0]}, fitness: {metric[0] / metric[1   ] * 100:2f}')
                    print(f"    counter: {counter + 1}/{end_row-start_row+1}, overlap: {overlap}")
                    print(f"    iteration time: {end_t - start} ")
                    local_counter += 1
                    counter += 1
                    if counter == len(range(end_row - start_row + 1)):
                        save_to_file(result[:local_counter], end_row-local_counter+1, end_row, output_dir, thresh)
                        continue
                    if counter % save_interval == 0:
                        partial_end_row = start_row+i

                        save_to_file(result, start_row+i-save_interval+1, partial_end_row, output_dir, thresh)
                        local_counter = 0
                        result = np.empty((save_interval, 10), dtype=object)


        finally:
            master.close()
    print(f'Tiempo total transcurrido: {time() - start_time}')


if __name__ == "__main__":
    main()
