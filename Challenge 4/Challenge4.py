from __future__ import division

from sklearn.model_selection import KFold
import random
import json
import dbSetup
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import normalize
import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import LogisticRegression
from sklearn import decomposition
from sklearn.svm import SVC
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
X_train = []
y_train = []
X_test = []
y_test = []
DLLs = []
feature_names = []
# feature_names.append("Size of sample")     # 0
feature_names.append("# of Exports")       # 1
feature_names.append("# of Imports")       # 2
feature_names.append("PEsecs(Size)")       # 3
feature_names.append("PESecs(VirtSize)")   # 4
feature_names.append("PESecs(Entropy)")    # 5
# feature_names.append("pehash")             # 6
feature_names.append("debug")              # 7
feature_names.append("rich_header")        # 8
'''
    Helper functions
'''
def undersample(data, how_many_extra_normal=0):
    new_data = []
    check_dict = {}

    #np.random.shuffle(data)

    for i in range(0, np.shape(data)[0]):
        if data[i][np.shape(data)[1] - 1] == 1:
            new_data.append(data[i].tolist())

    size_of_anomalies = len(new_data)

    break_while = True
    while(break_while):
        random_row_index = random.randint(0, np.shape(data)[0]-1)
        if random_row_index not in check_dict:
            if data[random_row_index][np.shape(data)[1] - 1] == 0:
                new_data.append(data[random_row_index])
                check_dict[random_row_index] = 1

                if (len(check_dict) == size_of_anomalies + how_many_extra_normal) or (len(check_dict) + size_of_anomalies == len(data)):
                    break_while = False

    new_data = np.array(new_data)
    np.random.shuffle(new_data)
    return np.array(new_data)


def get_filename(training):
    if training:
        filename = "data/training_set_dedup"
    else:
        filename = "data/test_set_dedup"

    return filename


def get_data(training):

    filename = get_filename(training)
    data = []
    with open(filename) as data_file:
        for row in data_file:
            j = json.loads(row)
            data.append(j)

    return data


def normalize_data(x,mode):
    if mode == 'l2':
        return normalize(x, norm='l2')
    else:
        return ((x - np.amin(x, axis = 0)) / x.ptp(0))


def check_json(json_obj, key):
    if key in json_obj and json_obj[key] != None:
        return True
    return False


def get_import_dlls(data):
    global DLLs
    for json_obj in data:
        if check_json(json_obj, "results"):
            json_obj = json_obj["results"]["peinfo"]
        else:
            json_obj = json_obj["peinfo"]
        if check_json(json_obj, "imports"):
            for import_dll in json_obj["imports"]:
               if import_dll["dll"].lower() not in DLLs:
                   DLLs.append(import_dll["dll"].lower())

    return DLLs


def process_data(data):
    processed_data = []
    global DLLs
    global feature_names



    for json_obj in data:
        processed_data_inner = []

        json_obj_orig = json_obj

        # processed_data_inner.append(len(json_obj))  # Feature 0

        if check_json(json_obj, "results"):
            json_obj = json_obj["results"]["peinfo"]
        else:
            json_obj = json_obj["peinfo"]

        #### Number of Exports ####
        if check_json(json_obj, "exports"):  # Feature 1
            processed_data_inner.append(len(json_obj["exports"]))
        else:
            processed_data_inner.append(0)

        #### Number of Imports ####
        if check_json(json_obj, "imports"):  # Feature 2
            processed_data_inner.append(len(json_obj["imports"]))
        else:
            processed_data_inner.append(0)

        #### All Training Data DLLs ####
        # if check_json(json_obj, "imports"):
        #     count = [0]* len(DLLs)
        #     for imports in json_obj["imports"]:
        #         if imports["dll"].lower() in DLLs:
        #            count[DLLs.index(imports["dll"].lower())] += 1
        #     for i in count:
        #         processed_data_inner.append(i)
        # else:
        #     for i in range(0,len(DLLs)):
        #         processed_data_inner.append(0)

        #### PESECTIONS ####
        if check_json(json_obj, "pe_sections"):
            size_array = []
            virt_size_array = []
            entropy_array = []

            for pe_section in json_obj["pe_sections"]:
                size_array.append(pe_section["size"])  # Feature 4
                virt_size_array.append(pe_section["virt_size"])  # Feature 5
                entropy_array.append(pe_section["entropy"])  # Feature 6

            if len(size_array) != 0:
                processed_data_inner.append(max(size_array))
            else:
                processed_data_inner.append(0)

            if len(virt_size_array) != 0:
                processed_data_inner.append(max(virt_size_array))
            else:
                processed_data_inner.append(-1)

            if len(entropy_array) != 0:
                processed_data_inner.append(max(entropy_array))
            else:
                processed_data_inner.append(-1)
        else:
            processed_data_inner.append(-1)
            processed_data_inner.append(-1)
            processed_data_inner.append(-1)

        # ### Pehash ####
        # if check_json(json_obj, "pehash"):  # Feature 7
        #     processed_data_inner.append(1)
        # else:
        #     processed_data_inner.append(0)

        #### Debug ####
        if check_json(json_obj, "debug"):  # Feature 8
            processed_data_inner.append(1)
        else:
            processed_data_inner.append(0)

        #### Rich Header ####
        times_used_array = []
        if check_json(json_obj, "rich_header"):
            if check_json(json_obj["rich_header"], "values_parsed"):
                for times_used in json_obj["rich_header"]["values_parsed"]:
                    times_used_array.append(times_used["times_used"])

                if len(times_used_array) != 0:
                    processed_data_inner.append(max(times_used_array))  # Feature 9
                else:
                    processed_data_inner.append(-1)
            else:
                processed_data_inner.append(-1)
        else:
            processed_data_inner.append(-1)


        #### Label ####
        if check_json(json_obj_orig, "label"):
            processed_data_inner.append(1 if json_obj_orig["label"] == "malicious" else 0)

        processed_data.append(np.array(processed_data_inner))

    processed_data = np.array(processed_data)
    print len(DLLs)
    print DLLs
    print np.shape(processed_data)
    return processed_data


def process_train_test():
    global X_train
    global y_train
    global X_test

    #np.random.shuffle(X_train)

    last_col_index = X_train.shape[1] - 1
    y_train = X_train[:, last_col_index]  # Last column in labels
    X_train = np.delete(X_train, -1, 1)  # delete last column of xtrain

    # X_train = normalize_data(X_train, "l22")
    # X_test = normalize_data(X_test, "l22")

    #scaler = StandardScaler()
     # Don't cheat - fit only on training data
    #scaler.fit(X_train)
    #X_train = scaler.transform(X_train)
     # apply same transformation to test data
    #X_test = scaler.transform(X_test)


def write_extended_features():
    global X_train
    global y_train
    global X_test
    global DLLs
    X_train = get_data(training=True)
    X_test = get_data(training=False)
    DLLs = get_import_dlls(X_train)
    X_train = process_data(X_train)
    X_test = process_data(X_test)

    # Binary data
    np.save('data/training_extended_binary.npy', X_train)
    np.save('data/testing_extended_binary.npy', X_test)
    np.savetxt("data/training_extended.csv", np.asarray(X_train), delimiter=",",fmt='%.2f')
    np.savetxt("data/testing_extended.csv", np.asarray(X_test), delimiter=",",fmt='%.2f')


def reset_data(with_undersampling=True, reset_extended=True):
    global X_train
    global y_train
    global X_test

    if reset_extended:
        write_extended_features()
    else:
        X_train = np.load("data/training_extended_binary.npy")
        X_test = np.load("data/testing_extended_binary.npy")
    if with_undersampling:
        X_train = undersample(X_train)
    process_train_test()


def import_data(train_mode):
    return dbSetup.getFeatures(train_mode)


def write_predictions_to_file(filename, data):
    f = open(filename, 'w')
    f.write('sha256,label\n')
    i = 0
    filename = get_filename(False)
    with open(filename) as data_file:
        for row in data_file:
            j = json.loads(row)
            f.write('%s' % j["sha256"])
            f.write(',')
            f.write('%s' % 'benign' if data[i] == 0 else 'malicious')
            f.write('\n')

            i = i + 1

    f.close()


def execute_classifier(use_training, clf, name, feature_importance=False):
    global feature_names

    print "Beginning evaluation of: " + name

    clf.fit(X_train, y_train)
    predictions = clf.predict(X_test)
    predictions = np.round(predictions)

    if feature_importance:
        importances = clf.feature_importances_
        std = np.std([tree.feature_importances_ for tree in clf.estimators_],
                     axis=0)
        indices = np.argsort(importances)[::-1]

        # Print the feature ranking
        print("Feature ranking:")

        for f in range(X_train.shape[1]):
            print("%d. feature %s (%f)" % (f + 1, feature_names[indices[f]], importances[indices[f]]))

        test = []
        for f in range(X_train.shape[1]):
            test.append(indices[f])

        print indices
        # Plot the feature importances of the forest
        plt.figure()
        plt.title("Feature importances (" + name + ")")
        plt.bar(range(X_train.shape[1]), importances[indices],
                color="r", yerr=std[indices], align="center")
        plt.xticks(range(X_train.shape[1]), indices)
        plt.xlim([-1, X_train.shape[1]])
        plt.show()

    if not use_training:
        return predictions
    else:
        accuracy = 0
        for i in range(0, len(predictions)):
            if predictions[i] == y_test[i]:
                accuracy += 1

        return accuracy/len(predictions)


def deleteColumnsPanda(pandaDataframe, blacklist):
    for element in blacklist:
        del pandaDataframe[element]
    return pandaDataframe


def visualize_anomalies():
    data = dbSetup.getFeatures(train_mode=True)
    data = deleteColumnsPanda(data,['id', 'proto','service','state'])

    data = data.as_matrix()

    data = undersample(data, how_many_extra_normal=-40)

    second_last_col_index = data.shape[1] - 2
    labels = data[:, second_last_col_index]
    data = np.delete(data, -1, 1)  # delete last column of xtrain
    data = np.delete(data, -1, 1)  # delete last column of xtrain

    # tsne = manifold.TSNE(n_components=3, init='pca', random_state=0)
    # Y = tsne.fit_transform(data)
    pca = decomposition.PCA(n_components=2)
    pca.fit(data)
    Y = pca.transform(data)

    plt.scatter(
        Y[:, 0], Y[:, 1], marker='o',
        cmap=plt.get_cmap('Spectral'))
    for label, x, y in zip(labels, Y[:, 0], Y[:, 1]):
        plt.annotate(
            label,
            xy=(x, y), xytext=(-20, 20),
            textcoords='offset points', ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

    plt.show()


def generic_numeric(clf_name,clf,instance,min,max,element):
    classifier = {}
    for i in range(min,max):
        tmp = clf()
        tmp.__setattr__(element,i)
        classifier["_".join((clf_name,element,str(i)))] = tmp
    return classifier


'''
    Main function. Start reading the code here
'''
def main():
    global training_data
    global testing_data
    global X_train
    global X_test
    global y_train
    global y_test

    reset_extended = False
    optimize_params = False
    undersample = True

    # visualize_anomalies()

    num_splits = 5

    kfold = KFold(n_splits=num_splits)
    if not optimize_params:
    # Define "classifiers" to be used
        classifiers = {
            #"ADA Boost" : AdaBoostClassifier(n_estimators=51),
            "Extra Trees" : ExtraTreesClassifier(n_estimators=35),
            "Random Forest": RandomForestClassifier(criterion="gini", n_estimators=35),

        }
    else:
        classifiers = generic_numeric("ExtraTreesClassifier",ExtraTreesClassifier, ExtraTreesClassifier(criterion="entropy"),1,100,'n_estimators')
        classifiers = generic_numeric("RandomForest",RandomForestClassifier,RandomForestClassifier(),1,100,'n_estimators')

    # Load data from dat file
    # unsupervised_technique(X_train, y_train, X_test, y_test, attack_cats)


    # Load data from dat file
    reset_data(reset_extended=reset_extended,with_undersampling=undersample)
    #X_train = normalize_data(X_train,'')
    #X_test = normalize_data(X_test,'')

    X_total = X_train
    y_total = y_train
    f = open('Accuracies.csv', 'w')
    for name, classifier in classifiers.items():
        accuracy = 0
        for train_index, test_index in kfold.split(X_total):
            # Use indices to seperate out training and test data
            X_train, X_test = X_total[train_index], X_total[test_index]
            y_train, y_test = y_total[train_index], y_total[test_index]

            accuracy += execute_classifier(True, classifier, name, feature_importance=False)


        total = accuracy / num_splits
        print "Accuracy of {} is {} %".format(name, round((total)*100, 5))
        f.write(name)
        f.write(',')
        f.write(str(round((total)*100, 5)))
        f.write('\n')
    f.close()

    reset_data(reset_extended=False,with_undersampling=undersample)

    # Use this loop for testing on test data
    if not optimize_params:
         for name, classifier in classifiers.items():
             y_test = execute_classifier(False, classifier, name, feature_importance=False)
             write_predictions_to_file(name + '_output.csv.dat', y_test)


if __name__ == "__main__":
    main()


            #"MLP500,250,10,100" : MLPClassifier(hidden_layer_sizes=(500,250,10,100)),
            #"MLP500,10,500" : MLPClassifier(hidden_layer_sizes=(500,10,500),warm_start=True, beta_1=0.999, beta_2=0.9900),
            #"MLP":MLPClassifier(batch_size=20, warm_start=True,beta_1=0.09, beta_2=0.09)
            #"DBSCAN":DBSCAN()
           # "MLPlogistic":MLPClassifier(hidden_layer_sizes=(500,100,10,2,500),activation='logistic',max_iter=1000),
            # "MLPtanh":MLPClassifier(activation='tanh',max_iter=1000),
            # "MLPidentity":MLPClassifier(activation='identity',max_iter=1000),
            # Baseline Traning: Accuracy of MLP is 91.71597 %
            # Accuracy of MLPlogistic is 87.8822 %
            # Accuracy of MLPtanh is 90.93701 %
            # Accuracy of MLP is 91.6445 %
            # Accuracy of MLPidentity is 86.42633 %
            # "KNN Classifier": KNeighborsClassifier(n_neighbors=5, metric='euclidean', p = 2),
            # "Logistic Regression": LogisticRegression(),
            # "KNN Regressor": KNeighborsRegressor(n_neighbors=5),
            #"SVCsigmoid" : SVC(kernel='sigmoid',C=5.0),
            #"SVCpoly":SVC(kernel='poly',degree= 2,C=3.0),
            #"SVC" : SVC(C=3.0)
