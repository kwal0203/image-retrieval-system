from sklearn.metrics.pairwise import euclidean_distances
import pandas as pd
import numpy as np
import csv


class Search:
    def __init__(self, search_config):
        self.metric = search_config['similarity_metric']
        self.index_path = search_config['input']
        self.features = None
        self.num_files = 0
        self.result = []
        self.names = []

    # Print results to screen/file
    def print_results(self):
        _map = round(self.result[0], 2)
        p_5 = round(self.result[1], 2)
        p_10 = round(self.result[2], 2)
        p_25 = round(self.result[3], 2)
        p_50 = round(self.result[4], 2)
        p_100 = round(self.result[5], 2)
        print("_map:  ", _map)
        print("p_5:   ", p_5)
        print("p_10:  ", p_10)
        print("p_25:  ", p_25)
        print("p_50:  ", p_50)
        print("p_100: ", p_100)
        # TODO: Find logging library compatible with Python 3.6
        # logging.info("----- RESULTS -----")
        # logging.info("{} {} {} {} {} {}".format(
        #         _map, p_5, p_10, p_25, p_50, p_100))

    # Create list of features in numpy array format. Do this so we don't
    # have to read the CSV file for each query.
    def read_index(self):
        print(self.index_path)
        with open(self.index_path) as f:
            # Get dimensions of input index file so we can allocate memory
            # (in self.features)
            # Note: the '-1' for feature_size is because the sum includes the
            # feature name
            reader = csv.reader(f, delimiter=',')
            feature_size = len(next(reader)) - 1
            f.seek(0)
            self.num_files = sum(1 for line in f)
            f.seek(0)
            self.features = np.zeros(shape=(self.num_files, feature_size))

            idx_count = 0
            for idx, row in enumerate(reader):
                self.features[idx] = np.array(row[1:])
                self.names.append(row[0])
                idx_count += 1
                if idx_count % 100 == 0:
                    print("[INFO] - Reading row {}".format(idx_count))

    # A distance matrix is computed from the whole set of image features. Each
    # column is sorted and various metrics calculated on the resulting list.
    def results_create(self):
        # 1. Read index into memory
        self.read_index()

        _row_names = self.names

        dist = euclidean_distances(self.features)
        print("Distance matrix calculation finished")

        distance_df = pd.DataFrame(dist, index=_row_names, columns=_row_names)
        print("Data-frame construction finished")

        _map = 0
        map_count = 0

        # Dictionary to store precision at k values as they are calculated.
        # All values initialized to 0 to begin with.
        # k_list = [5, 10, 25, 50, 100, 250, 500, 750, 1000]
        k_list = [5, 10, 25, 50, 100, 250, 500]
        prec_arr = {i: 0 for i in k_list}

        for col_idx, col_name in enumerate(distance_df.columns):
            feature = distance_df.loc[col_name]
            image_class = ''.join([x for x in col_name if not x.isdigit()])

            # Sort retrieval results and discard the first item (this is the
            # query feature itself). We then map the sorted results to 0's and
            # 1's depending on if the given item is in the same class as the
            # query.
            sorted_df = feature.sort_values()[1:]
            preds = [1 if image_class in j else 0 for j in sorted_df.index]

            # print(sorted_df.shape)
            # print(sorted_df[:10])
            # print(preds[:10])
            # print("Image name:  ", col_name)
            # print("Image class: ", image_class)
            # sys.exit()

            # Precision list
            prec_at_k_list = []
            hit = 0

            # Store intermediate calculations for MAP and P@K
            for idx, pred in enumerate(preds):
                _idx = idx + 1

                # For MAP calculation
                if pred == 1:
                    hit += 1
                    prec_at_k_list.append(hit / _idx)

                # For P@K calculations
                if _idx in prec_arr:
                    prec_arr[_idx] += (hit / _idx)

            if len(prec_at_k_list) > 0:
                average_precision = np.mean(prec_at_k_list)
            else:
                average_precision = 0

            _map += average_precision
            map_count += 1

            if map_count % 100 == 0:
                print("[INFO] - Query number: {}".format(map_count))

        _map /= map_count
        _map *= 100

        # Store final results in a list then call print function
        self.result.append(_map)
        for k in k_list:
            self.result.append(100 * (prec_arr[k] / self.num_files))

        self.print_results()

