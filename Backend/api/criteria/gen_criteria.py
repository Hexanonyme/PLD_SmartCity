#
from ..fs.fs import load_database_psd
from ..algorithm.algorithm import closest_record
from ..algorithm.algorithm import density_around
from ..debug.debug import watch_time
from ..algorithm.algorithm import records_around
#


def rank(spec):
    """
        Calcul la note pour un critère donné avec les specifications reçues

        Paramètres:
            TODO

        Retour:
            retourne un triplet (note_sur_dix, element_trouvé, (densité|None))
    """
    typ = spec['criteria']['type']
    if typ == 'distance_based':
        return distance_based(spec['criteria'], spec['coordinates'],spec['dist'])
    elif typ == 'density_based':
        return density_based(spec['criteria'], spec['coordinates'],spec['dens'])
    elif typ == 'dist_dens_based':
        return dist_dens_based(spec['criteria'], spec['coordinates'],spec['dens'],spec['dist'])
    elif typ == 'custom':
        return custom(spec['criteria'], spec['coordinates'])
    else:
        return (None, None, None)  # error case


# @watch_time
def distance_based(criteria, coord, min_max_dist):
    """
        Calcul de distance générique

        Paramètres:
            TODO

        Retour:
            retourne un triplet (note_sur_dix, element_trouvé, (densité|None))
    """
    # récupération et calcul des paramètres
    if min_max_dist:
        min_dist = min_max_dist[0]
        max_dist = min_max_dist[1]
    else:
        max_dist = criteria['params']['max_dist']
        min_dist = criteria['params']['min_dist']
    scale = criteria['params']['dist_scale']
    # lecture dans la base
    records = load_database_psd(criteria['name'])
    # création de la note vide
    mark = -1.0
    if not records:
        print('[gen_criteria.distance_based]> %s' % criteria['name'])
    else:
        # récupération du point le plus proche
        dist, record = closest_record(records, coord)
        # vérification d'appartenance à l'anneau
        if dist < min_dist or dist > max_dist:
            # le lieu le plus proche n'est pas dans l'anneau, on retourne 0
            mark = 0.0
            record = None
        # calcul de la note en fonction de l'échelle
        else:
            if scale == 'log':
                # todo
                mark = -1.0
            elif scale == 'linear':
                mark = 10.0 * (1.0 - ((dist - min_dist) / (max_dist - min_dist)))
            # else: mark = None (cf. initialisation de mark)
    # finally return mark and record for details
    return (mark, record, None)


# @watch_time
def density_based(criteria, coord, min_max_dens):
    """
        Calcul de densité générique

        Paramètres:
            TODO

        Retour:
            retourne un triplet (note_sur_dix, element_trouvé, (densité|None))
    """
    # récupération et calcul des paramètres
    if min_max_dens:
        min_density = min_max_dens[0]
        max_density = min_max_dens[1]
    else:
        max_density = criteria['params']['max_density']
        min_density = criteria['params']['min_density']
    radius = criteria['params']['radius']
    scale = criteria['params']['dens_scale']
    # lecture dans la base
    records = load_database_psd(criteria['name'])
    # création de la note vide
    mark = -1.0
    closest = None
    if not records:
        print('[gen_criteria.density_based]> %s' % criteria['name'])
    else:
        # récupération de la densité
        density, closest, min_dist = density_around(records, coord, radius)
        # vérification d'appartenance à l'anneau
        if density < min_density:
            mark = 10 * (density / min_density)
            closest = None
        elif density > max_density:
            if density > max_density + min_density:
                mark = 0.0
            else:
                mark = 10 * ((max_density + min_density - density) / min_density)
        # calcul de la note en fonction de l'échelle
        else:
            mark = 10.0
    # finally return mark and record for details
    return (mark, closest, density)


# @watch_time
def dist_dens_based(criteria, coord, min_max_dens, min_max_dist):
    """
        Calcul générique couplage de distance et densité

        Paramètres:
            TODO

        Retour:
            retourne un triplet (note_sur_dix, element_trouvé, (densité|None))
    """
    mark_density, record, density = density_based(criteria, coord, min_max_dens)
    mark_dist, closest, empty = distance_based(criteria, coord, min_max_dist)
    mark = (criteria['params']['dist_coeff'] * mark_dist + criteria['params']['dens_coeff'] * mark_density) / (criteria['params']['dist_coeff'] + criteria['params']['dens_coeff'])
    return (mark, closest, density)


# @watch_time
def custom(criteria, coord):
    """
        Calcul customisé pour les données spéciales

        Paramètres:
            TODO

        Retour:
            retourne un triplet (note_sur_dix, element_trouvé, (densité|None))
    """
    if criteria['name'] == "bruit":
        return custom_bruit(criteria, coord)
    else:
        print('[gen_criteria.py|custom]> /!\ Profil custom non disponible /!\\')
        return(-1.0, None, None)


# @watch_time
def custom_bruit(criteria, coord):
    """
        Calcul customisé pour le bruit

        Paramètres:
            TODO

        Retour:
            TODO
    """
    # récupération du rayon
    radius = criteria['params']['radius']
    max_bruit = criteria['params']['max']
    min_bruit =criteria['params']['min']
    # lecture dans la base
    records_db = load_database_psd(criteria['name'])
    # récupération des records les plus proches
    records = records_around(records_db, coord, radius)
    # initialisation de la note
    mark = -1.0
    if not records:
        print('[gen_criteria.py|custom_bruit]> no record found around for %s' % criteria['name'])
    else:
        records_size = len(records)
        # création des variables necessaires au traitement
        s = 0
        for record in records:
            niveau_bruit = record['data']['value']
            print(niveau_bruit)
            note_bruit = 10 * (1.0 - ((niveau_bruit - min_bruit) / (max_bruit - min_bruit)))
            print(note_bruit)
            s += note_bruit
        mark = s / records_size
    # on retourne la note et pas de record
    return (mark, None, None)
