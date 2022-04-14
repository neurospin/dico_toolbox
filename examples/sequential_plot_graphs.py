import dico_toolbox as dtb
import os
import glob
import pandas as pd
from soma import aims

import keypress

# database_path = "/nfs/neurospin/dico/data/bv_databases/human/partially_labeled/paracingular/tissier_2018/subjects"
database_path = "/nfs/neurospin/dico/data/bv_databases/human/partially_labeled/paracingular/arnaudMar2015_data/graph.manual.acc/COSSIB/sujets_cossib"
subpath = "t1mri/default_acquisition/default_analysis/folds/3.1/default_session_manual"
csv_file=None
parameter_name=None
true_value=None
# csv_file = "/neurospin/dico/data/bv_databases/human/partially_labeled/paracingular/tissier_2018_labels.csv"
# parameter_name = 'ACC_right_2levels_new'
# true_value = 'present'
number_windows = 2

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

    subjects_dict = {}

    print('Reading graphs...', end='', flush=True)
    for sub in subjects[:10]:
        sub = os.path.basename(sub)
        # print(sub.split('_')[0])
        if selected_subjects is None:
            graph_filename = f"{database_path}/{sub}/{subpath}/R{sub}_default_session_manual.arg"
            subjects_dict[sub] = aims.read(graph_filename)
        else:           
            if sub.split('_')[0] in selected_subjects:
                graph_filename = f"{database_path}/{sub}/{subpath}/R{sub}_default_session_manual.arg"
                subjects_dict[sub] = aims.read(graph_filename)
    print('done')

    nb_subjects = len(subjects_dict)
        
    if nb_subjects == 0:
        raise ValueError(f"No graph detected in {database_path}")

    print(f"Number of detected subjects = {len(subjects_dict)}")
    
    return subjects_dict

def get_selected_subjects():
    """Returns subjects  whose parameter_name has the true_value.
    
    Return:
        selected_subjects: list
    """
    if not os.path.isfile(csv_file):
        raise FileNotFoundError(csv_file)
    csv = pd.read_csv(csv_file)
    csv = csv[['Sujet', parameter_name]]
    csv = csv.set_index('Sujet')
    selected_subjects = list(csv[csv[parameter_name]==true_value].index)
    print(f"Selected subjects = {selected_subjects}")
    return selected_subjects
    

def create_anatomist_block():
    """Create anatomist block with desirec number of windows"""
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
    an.new_window_block(windows=windows)
    print('done')

def sequential_plot_graphs(subjects_dict):
    global an
    window_names = an.blocks["DefaultBlock"].windows
    nb_subjects = len(subjects_dict)
    # Gets color map for sulcus
    sh = aims.carto.Paths.shfjShared()
    colors = aims.read(os.path.join(sh, 'nomenclature', 'hierarchy',
                                    'sulcal_root_colors.hie'))   
    
    first_item=0
    last_item=min(first_item+number_windows-1, nb_subjects)

    # Mains loop that successively displays graphs
    while (1):
        # Takes next number_windows element of dictionary
        d = dict(list(subjects_dict.items())[first_item:(last_item+1)])
        
        # Add these selected graphs to window
        for (cnt, name_graph), window_name in zip(enumerate(d), window_names):
            print(cnt, name_graph)
            an.add_objects_to_window({'colors': colors}, window_name=window_name)
            an.add_objects_to_window({name_graph: d[name_graph]}, window_name=window_name)
        
        input("\nPress Enter\n")
        keypress.wait_for_keypress()

        for window_name in window_names:
            an.clear_window(window_name)
            
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






