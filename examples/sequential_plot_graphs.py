import dico_toolbox as dtb
import os
import glob
from time import time
import pandas as pd
import numpy as np
from soma import aims

import keypress

database = 'pclean'
# database = 'HCP'
# database = 'tissier_2018_none'
# database = 'arnaud_cossib'
# database = 'arnaud_cos'
# database = 'arnaud_nv'

if database == 'pclean':
    database_path = "/neurospin/dico/data/bv_databases/human/manually_labeled/pclean/all"
    subpath = "t1mri/t1/default_analysis/folds/3.3/base2023_manual"
    csv_file = None
    subject_name = None
    parameter_name = None
    true_value = None
elif database == 'HCP':
    database_path = "/neurospin/dico/data/bv_databases/human/not_labeled/hcp/hcp"
    subpath = "t1mri/BL/default_analysis/folds/3.1"
    csv_file = "/neurospin/dico/data/bv_databases/human/not_labeled/hcp/participants.csv"
    subject_name = 'Subject'
    parameter_name = 'QC_Issue'
    true_value = float("nan")
elif database == 'tissier_2018':
    database_path = "/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/tissier_2018/subjects"
    subpath = "t1mri/default_acquisition/default_analysis/folds/3.1/default_session_manual"
    csv_file = "/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/tissier_2018_labels.csv"
    subject_name = 'Sujet'
    parameter_name = 'ACC_right_2levels_new'
    true_value = 'present'
elif database == 'tissier_2018_none':
    database_path = "/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/tissier_2018/subjects"
    subpath = "t1mri/default_acquisition/default_analysis/folds/3.1/default_session_manual"
    csv_file = None
    subject_name = 'Sujet'
    parameter_name = None
    true_value = None
elif database == 'arnaud_cossib':
    database_path = "/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/arnaudMar2015_data/graph.manual.acc/COSSIB/sujets_cossib"
    subpath = "t1mri/default_acquisition/default_analysis/folds/3.1/default_session_manual"
    subject_name = 'IRM_NAME1'
    csv_file="/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/sujets_cossib.csv"
    parameter_name='PCS_R1'
    true_value='pro'
elif database == 'arnaud_cos':
    database_path = "/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/arnaudMar2015_data/graph.manual.acc/COS/sujets_cos"
    subpath = "t1mri/default_acquisition/default_analysis/folds/3.1/default_session_manual"
    subject_name = 'IRM_NAME1'
    csv_file="/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/sujets_cos.csv"
    parameter_name='PCS_R1'
    true_value='pro'
elif database == 'arnaud_nv':
    database_path = "/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/arnaudMar2015_data/graph.manual.acc/NV/sujets_nv"
    subpath = "t1mri/default_acquisition/default_analysis/folds/3.1/default_session_manual"
    subject_name = 'IRM_NAME1'
    csv_file="/neurospin/dico/data/bv_databases/human/partially_labeled/ACCpatterns/sujets_nv.csv"
    parameter_name='PCS2_R1'
    true_value='pre'
else:
    raise ValueError("You must specify a database")

number_windows = 3

an = None

def get_graphs(selected_subjects=None):
    """Gets graphs and returns a dictionary {subject: aims.Graph}"""
    if not os.path.isdir(database_path):
        raise NotADirectoryError(database_path)

    print('Listing subjects...', end='', flush=True)
    subjects = glob.glob(f"{database_path}/*[!.minf|.sqlite|.html]")
    print('done')

    if len(subjects) == 0:
        raise ValueError(f"No subject detected in {database_path}")

    if selected_subjects:
        print(f"selected_subjects[:10] = {selected_subjects[:10]}")

    subjects_dict = {}

    print('Reading graphs...', end='', flush=True)
    for sub in subjects[:10]:
        sub = os.path.basename(sub)
        print(sub)
        # print(sub.split('_')[0])
        if selected_subjects is None:
            graph_filename = f"{database_path}/{sub}/{subpath}/R{sub}*.arg"
            graph_filename = glob.glob(graph_filename)[0]
            print(f"graph_filename = {graph_filename}")
            subjects_dict[sub] = aims.read(graph_filename)
        else: 
            if database == 'tissier_2018':
                choice_subject =  sub.split('_')[0]
            elif database == 'HCP':
                choice_subject = sub
            else:
                sub_list = sub.split('_')[:-1]
                choice_subject = '_'.join(sub_list)         
            print(f"choice_subject = {choice_subject}")
            if choice_subject in selected_subjects:
                graph_filename = f"{database_path}/{sub}/{subpath}/R{sub}*.arg"
                print(f"graph_filename = {graph_filename}")
                graph_filename = glob.glob(graph_filename)[0]
                print(f"graph_filename = {graph_filename}")
                subjects_dict[sub] = aims.read(graph_filename)
    print('done')

    nb_subjects = len(subjects_dict)
        
    if nb_subjects == 0:
        raise ValueError(f"No graph detected in {database_path}")

    print(f"Number of detected subjects = {len(subjects_dict)}")
    
    return subjects_dict

def is_equal(a, true_value):
    if np.isnan(true_value):
        if np.isnan(a):
            return True
        else:
            return False
    else:
        return (a==true_value)

def get_selected_subjects():
    """Returns subjects  whose parameter_name has the true_value.
    
    Return:
        selected_subjects: list
    """
    if not os.path.isfile(csv_file):
        raise FileNotFoundError(csv_file)
    csv = pd.read_csv(csv_file)
    csv = csv[[subject_name, parameter_name]]
    csv = csv.set_index(subject_name)
    csv2 = csv
    if np.isnan(true_value):
        selected_subjects = list(csv[csv[parameter_name].isna()].index.astype(str))
    else:
        selected_subjects = list(csv[csv[parameter_name]==true_value].index.astype(str))
    print(f"Selected subjects = {selected_subjects}")
    return selected_subjects
    

def create_anatomist_block():
    """Create anatomist block with desired number of windows"""
    global an
    # run this code only once, at the beginning.
    print('Opening anatomist...')
    an = dtb.anatomist.Anatomist()
    print('Opening anatomist...Done')

    # get the instance of the anatomist object
    anatomist_instance = an.get_anatomist_instance()
    print(anatomist_instance.getVersion())

    # Creates a block with number_windows windows
    windows = ("3D",)*number_windows

    print('Creating anatomist block...', end='')
    an.new_window_block(windows=windows, columns=number_windows)
    print('done')


def sequential_plot_graphs(subjects_dict):
    """Sequentially plots graph upon keypress"""

    global an
    window_names = an.blocks["DefaultBlock"].windows
    nb_subjects = len(subjects_dict)
    # Gets color map for sulcus
    sh = aims.carto.Paths.shfjShared()
    colors = aims.read(os.path.join(sh, 'nomenclature', 'hierarchy',
                                    'sulcal_root_colors.hie'))   
    
    first_item=0
    last_item=min(first_item+number_windows-1, nb_subjects)

    print(f"\nThere are {nb_subjects} subjects to display")

    print('Adding objects to anatomist...', end='', flush=True)
    an.add_objects_to_anatomist({'colors': colors}, keep_objects=True)
    an.add_objects_to_anatomist(subjects_dict, keep_objects=True)
    print("done")

    # Mains loop that successively displays graphs
    while (1):
        # Takes next number_windows element of dictionary
        d = dict(list(subjects_dict.items())[first_item:(last_item+1)])

        t1 = time()
        # Add these selected graphs to window
        for (cnt, name_graph), window_name in zip(enumerate(d), window_names):
            print(cnt, name_graph)
            an.add_objects_to_window({'colors': colors}, window_name=window_name, keep_objects=True)
            an.add_objects_to_window({name_graph: d[name_graph]}, window_name=window_name, keep_objects=True)
        print(f"Adding objects to windows took {time()-t1} seconds")        

        input("\nPress Enter\n")
        keypress.wait_for_keypress()

        t1 = time()
        # for window_name in window_names:
        #     an.clear_window(window_name)
        an.clear_windows(window_name_list=window_names)
        print(f"Clearing windows took {time()-t1} seconds")
            
        if keypress.choice == 'end':
            print("Quitting now")
            break
        elif keypress.choice == 'forward':
            print("Displays next graphs")
            first_item = first_item+number_windows if first_item+number_windows < nb_subjects else 0
            last_item=min(first_item+number_windows-1, nb_subjects-1)
        elif keypress.choice == "backward":
            print("Displays previous graphs")
            first_item = first_item-number_windows if first_item-number_windows >= 0 else nb_subjects-nb_subjects%number_windows
            last_item=min(first_item+number_windows-1, nb_subjects-1)


def delete_anatomist_block():
    an.delete_all_objects()


def main():
    if csv_file:
        selected_subjects= get_selected_subjects()
    else:
        selected_subjects=None
    subjects_dict = get_graphs(selected_subjects)
    create_anatomist_block()
    sequential_plot_graphs(subjects_dict)
    delete_anatomist_block()


# an.clear_block()

# an.close()

if __name__ == "__main__":
    main()







