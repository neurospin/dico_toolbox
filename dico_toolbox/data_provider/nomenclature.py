from .json_data import JsonData
import urllib.request

DATAFILE_PATHS = dict(
  sulci_regions_overlap="https://raw.githubusercontent.com/brainvisa/brainvisa-share/master/nomenclature/translation/sulci_regions_overlap.json"
)

class SulciRegionOverlap(JsonData):
  """Custom defined regions for sulcii studies.

  Region overlaps are allowed:
    - The same sulcus can appear in different regions.
    - Some regions incorporate more than one sulcus

  Properties:
    - regions (dict of str:dict) contains the regions definition.
      The keys of regions items correspond to the name of the regions.
      The values of regions lists of sulcii labels, as defined in the set of labels of the automatic-detection
  
  
  [ORIGINAL DESCRIPTION BY DENIS RIVIERE]
  On a choisi avec Jeff une liste de régions sulcales qui permet de faire
  des études région par région et qui au total recouvre tout le cerveau.
  C'est inspiré d'une liste que Clara nous a passée, mais ici on s'autorise des overlaps:
  certains sillons apparaissent dans plusieurs régions, et on a des régions qui recouvrent
  plusieurs grands sillons (par ex pour étudier un gyrus, voire un lobule).
  
  Je viens de le mettre sous forme de fichier .json dans le format reconnu par le traitement
  de morphométrie de Clara, même si ici on va l'utiliser dans un autre cadre. C'est un dictionnaire à 3 niveaux
  - le 1er niveau est toujours "brain" et contient dont 1 seule entrée
  - le 2e niveau correspond aux régions qu'on vient de définir. On a 44 régions par hémisphère, soit 88 en tout
  - le 3e niveau correspond aux sillons de la nomenclature de la reconnaissance automatique,
    ce sont ceux qui sont inclus dans la région. Ce sont aussi des clefs de dictionnaire, avec comme valeur une liste,
    qui reprend en fait le même nom ici (le format était un peu plus générique et autorisait de faire des 
    regroupements à plus bas niveau).
  """

  

  def __init__(self):
    # get regions data
    with urllib.request.urlopen(DATAFILE_PATHS["sulci_regions_overlap"]) as url:
      json_string = url.read().decode()

    super().__init__(json_string)
    self.regions = {k:list(v.keys()) for k,v in self.data['brain'].items()}

  def filter_regions(self, regular_expression):
    """Filter the regions"""
    return self._filter(regular_expression, self.regions) 

  def get_sulcii_in_region(self, region_name):
    """Return the labels of the sulci covered by the specified region"""
    return list(self.regions[region_name])

  @property
  def region_names(self):
    """The names of the custom regions"""
    return list(self.regions.keys())

  @property
  def regions_left(self):
    """all regions of the left hemisphere"""
    return self._filter("left", self.regions)

  @property
  def regions_right(self):
    """all regions of the right hemisphere"""
    return self._filter("right", self.regions)
  
  def __repr__(self):
    return f"Nomenclature of Region Overlaps. Defines {len(self.regions)} regions"


if __name__ == "__main__":
  sro = SulciRegionOverlap()
  
  print(sro.regions)