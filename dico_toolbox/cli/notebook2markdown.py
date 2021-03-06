import argparse
import re
import os
import shutil
import glob
import subprocess
import tempfile


def convert_notebook(nb_path, out_dir='.'):
    """System call jupyter-convert for markdown generation."""
    cmd = ['jupyter-nbconvert', nb_path, '--to',
           'markdown', '--output-dir', out_dir]
    task = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = task.communicate()

    if task.returncode != 0:
        raise(RuntimeError(stderr.decode()))


def comment_code_cells_by_keyword(markdown, *keywords):
    """Comment code cells that contain the specified text.
    The cells will disappear from markdown rendering.

    Args:
        markdown (str): the input markdown
        keywords (str) : the keywords

    Returns:
        str: A new version of the input markdown with removed cells.
    """
    out = markdown

    if len(keywords) > 0:
        kwds = '|'.join(keywords)
        regex = re.compile(
            "(?P<cell>```[^`]*({})[^`]*```)".format(kwds))
        out = regex.sub(
            "<!-- REMOVED CODE CELL [kw: {}]\n\g<cell>\n-->".format(kwds), markdown)

    return out


def comment_all_code_cells(markdown):
    """Comment code cells.
    The cells will disappear from markdown rendering.

    Args:
        markdown (str): the input markdown

    Returns:
        str: A new version of the input markdown with removed cells.
    """
    regex = re.compile("(?P<cell>```[^`]*```)")
    out = regex.sub("<!-- REMOVED CODE CELL\n\g<cell>\n-->", markdown)
    return out


def comment_empty_code_cells(markdown):
    """Comment empty code cells in the given markdown formatted string.
    The cells will disappear from markdown rendering.

    Args:
        markdown (_type_): the input markdown content

    Returns:
        markdown: A new version of the input markdown with removed cells.
    """
    regex = re.compile("```.*\n\n```")
    out = regex.sub("<!-- REMOVED EMPTY CODE CELL -->", markdown)
    return out


def correct_img_paths(markdown, old, new):
    """Correct the paths in images links

    Args:
        markdown (str): the input markdown content
        old (str): the old path of the images
        new (str): the new path of the images

    Returns:
        str: A new version of the input markdown with corrected images paths.
    """
    regex = re.compile(
        r"!\[(?P<text>.*?)\]\({}/(?P<filename>.*?)\)".format(old))
    out = regex.sub("![\g<text>]({}/\g<filename>)".format(new), markdown)
    return out


def main(*args, **kwargs):
    parser = argparse.ArgumentParser(
        description="Convert a notebook into a markdown file.\
            Hide cells containing the autorelaod magic command or the comment #HIDE_IN_MARKDOWN.")
    parser.add_argument(
        "input_path", help="The path of the Juptyter notebook to be converted", type=str)
    parser.add_argument("-o", "--output_path", default=None,
                        help="The path of the output markdown files, specified as '[output_path]/filename.md'. Default ./NOTEBOOK.md", type=str)
    parser.add_argument("-i", "--output_image_folder", default=None,
                        help="The path to the folder that will contain the images linked in the markdown. This path will be added to [output_path]. Default [output_path]/NOTEBOOK_files/", type=str)
    parser.add_argument("-c", "--no_code_cells", help="Remove all code cells.",
                        default=False, action="store_true")
    parser.add_argument("-e", "--keep_empty_cells", help="Keep empty code cells.",
                        default=True, action="store_false")
    parser.add_argument("-k", "--keyword", help="Remove the cells containing the specified keywords (use quotes to specify the keywords)", nargs='+', default=[],
                        type=str,)
    parser.add_argument("-a", "--keep_auto_hidden",
                        help="Keep the automatically hidden cells.\
                            If this flag is not active, cells containing\
                            the autorelaod magic command or #README_HIDE_CELL comment\
                            will be hidden", default=False, action="store_true")

    args = parser.parse_args()

    input_path = args.input_path
    assert os.path.isfile(input_path), f"ERROR: {input_path} file not found"
    output_path = args.output_path
    img_dir = args.output_image_folder
    keywords = args.keyword

    notebook_name = os.path.splitext(os.path.basename(input_path))[0]

    temp_dir = tempfile.mkdtemp()
    temp_img_dir = os.path.join(temp_dir, f"{notebook_name}_files")

    if output_path is None:
        output_path = "./NOTEBOOK.md"

    output_folder, output_notebook_name = os.path.split(
        os.path.splitext(output_path)[0])

    if output_folder == '':
        output_folder = '.'

    os.makedirs(output_folder, exist_ok=True)  # make the conversion folder

    if img_dir is None:
        img_dir = f"{output_notebook_name}_files"

    # convert jupyter notebook
    convert_notebook(input_path, temp_dir)

    # read the exported markdown
    with open(os.path.join(temp_dir, f"{notebook_name}.md"), 'r') as f:
        markdown = f.read()

    # eliminate unwanted code cells
    if args.no_code_cells:
        print("Remove all code cells.")
        markdown = comment_all_code_cells(markdown)
    else:
        if len(keywords) > 0:
            print("Remove cells by keyword.", keywords)
            markdown = comment_code_cells_by_keyword(
                markdown, *keywords)

        if not args.keep_empty_cells:
            print("Keep empty conde cells.")
            markdown = comment_empty_code_cells(markdown)

        if not args.keep_auto_hidden:
            markdown = comment_code_cells_by_keyword(
                markdown, '%autoreload', '#HIDE_IN_MARKDOWN')

    # IMAGE PATHS
    print("Move images and update paths.")
    # make the output image dir
    os.makedirs(img_dir, exist_ok=True)
    # change the paths in the markdown file
    old_img_dir = f"{notebook_name}_files"
    markdown = correct_img_paths(
        markdown, old_img_dir, img_dir.replace(output_folder, '.'))
    # copy the images
    for path in glob.glob(os.path.join(temp_img_dir, "*")):
        shutil.copy(path, img_dir)

    # write the new markdown
    with open(output_path, 'w') as f:
        f.write(markdown)
        shutil.rmtree(temp_dir)
