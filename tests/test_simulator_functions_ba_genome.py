import h5py
import pytest
import sys
from os import path
# Add the alts directory to the Python path
sys.path.append(path.join(path.dirname(__file__), '..'))
from simulator import Simulation
from simulator import Individual
import random
import numpy as np


# [0        #0:  Generations in the simulation (First generation is number 0)
#  1,       #1:  Number of groups in the population
#  20,      #2:  Mean number of individuals inside each group
#  0,       #3:  Standard deviation of number of individual per group
#  0,       #4:  Proportion of migration per groups in each generation
#  0,       #5:  Proportion of emigrants of the whole population
#  0,       #6:  Proportion of immigrants of the whole population
#  None,    #7:  Default phenotype for immigrants
#  1,       #8:  Mean life expectancy
#  0,       #9:  Standard deviation of the life expectancy
#  1,       #10: Survival probability assigned to each individual at the beginning of the generation
#  3,       #11: Generations taking into account in individuals' ancestry
#  10]      #12: Size of the genome


# Randomizes individual's genotype based on initial locus frequencies
@pytest.mark.parametrize('general_configuration, model_configuration, expected_result', [
    ([0, 1, 20, 0, 0, 0, 0, None, 1, 0, 1, 3, 10],
     {'module': {'name': 'blind_altruism'},
      'behaviour': {'alleles': 'selfish > altruistic',
                    'initial_frequencies': '1, 0',
                    'locus_size': '0',
                    'mutation_rate': '0',
                    'recombination_rate': '0'},
      'neutral': {'alleles': 'neutral > neutral',
                  'initial_frequencies': '0.5, 0.5',
                  'locus_size': '0',
                  'mutation_rate': '0',
                  'recombination_rate': '0'}},
     {"[['selfish', 'selfish'], ['neutral', 'neutral']]": 1,
      "[['selfish', 'altruistic'], ['neutral', 'neutral']]": 0,
      "[['altruistic', 'selfish'], ['neutral', 'neutral']]": 0,
      "[['altruistic', 'altruistic'], ['neutral', 'neutral']]": 0}
     ),
    ([0, 1, 20, 0, 0, 0, 0, None, 1, 0, 1, 3, 10],
     {'module': {'name': 'blind_altruism'},
      'behaviour': {'alleles': 'altruistic > selfish',
                    'initial_frequencies': '0.5, 0.5',
                    'locus_size': '0',
                    'mutation_rate': '0',
                    'recombination_rate': '0'},
      'neutral': {'alleles': 'neutral > neutral',
                  'initial_frequencies': '0.5, 0.5',
                  'locus_size': '0',
                  'mutation_rate': '0',
                  'recombination_rate': '0'}},
     {"[['selfish', 'selfish'], ['neutral', 'neutral']]": 0.25,
      "[['selfish', 'altruistic'], ['neutral', 'neutral']]": 0.25,
      "[['altruistic', 'selfish'], ['neutral', 'neutral']]": 0.25,
      "[['altruistic', 'altruistic'], ['neutral', 'neutral']]": 0.25}
     ),
    ([0, 1, 20, 0, 0, 0, 0, None, 1, 0, 1, 3, 10],
     {'module': {'name': 'blind_altruism'},
      'behaviour': {'alleles': 'selfish = altruistic',
                    'initial_frequencies': '0, 1',
                    'locus_size': '0',
                    'mutation_rate': '0',
                    'recombination_rate': '0'},
      'neutral': {'alleles': 'neutral > neutral',
                  'initial_frequencies': '0.5, 0.5',
                  'locus_size': '0',
                  'mutation_rate': '0',
                  'recombination_rate': '0'}},
     {"[['selfish', 'selfish'], ['neutral', 'neutral']]": 0,
      "[['selfish', 'altruistic'], ['neutral', 'neutral']]": 0,
      "[['altruistic', 'selfish'], ['neutral', 'neutral']]": 0,
      "[['altruistic', 'altruistic'], ['neutral', 'neutral']]": 1}
     )
])
def test_generate_individual_genotype_bag(general_configuration, model_configuration, expected_result):
    # random.seed(829504)
    simulation = Simulation(*general_configuration, model_configuration)
    genotypes_dictionary = {"[['selfish', 'selfish'], ['neutral', 'neutral']]": 0,
                            "[['selfish', 'altruistic'], ['neutral', 'neutral']]": 0,
                            "[['altruistic', 'selfish'], ['neutral', 'neutral']]": 0,
                            "[['altruistic', 'altruistic'], ['neutral', 'neutral']]": 0}
    replicas = 5000
    for i in range(replicas):
        genotype = str(simulation.generate_individual_genotype())
        genotypes_dictionary[genotype] += 1
    # Transform counts to proportions
    genotypes_dictionary = {k: v / replicas for _ in (sum(genotypes_dictionary.values()),)
                            for k, v in genotypes_dictionary.items()}
    assert genotypes_dictionary == pytest.approx(expected_result, rel=0.1)


@pytest.mark.parametrize('general_configuration, expected_mean, expected_sd', [
    ([0, 1000, 20, 1, 0, 1, 0, None, 1, 0, 1, 3, 10],
     20, 1),
    ([0, 20, 5, 0, 0, 1, 0, None, 1, 0, 1, 3, 10],
     5, 0),
])
def test_populate_groups_bag(general_configuration, expected_mean, expected_sd, ba_dom_model_configuration):
    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    sizes = []
    for group in simulation.groups:
        sizes.append(len(group))
    mean = np.mean(sizes)
    sd = np.std(sizes)
    assert mean == pytest.approx(expected_mean, rel=0.15)
    assert sd == pytest.approx(expected_sd, rel=0.15)


def test_save_generation_0_data(ba_dom_model_configuration):
    np.random.seed(665416)
    random.seed(665416)
    general_configuration = [1, 2, 10, 0, 0, 0, 0, None, 10, 0, 1, 3, 10]
    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    for i in range(1):
        simulation.pass_generation()
    with h5py.File('simulation_output.h5', 'a') as f:
        survivors = list(f['generation_0/survivors'][:])
        group_0 = list(f['generation_0/group'][:])
        group_1 = list(f['generation_1/group'][:])
        phenotype_0 = list(f['generation_0/phenotype'][:])
        phenotype_1 = list(f['generation_1/phenotype'][:])
        locus_neutral_0 = list(f['generation_0/locus_neutral'][:])
        locus_neutral_1 = list(f['generation_1/locus_neutral'][:])
        locus_behaviour_0 = list(f['generation_0/locus_behaviour'][:])
        locus_behaviour_1 = list(f['generation_1/locus_behaviour'][:])
    expected_survivors = list(np.ones(20))
    expected_group = list(np.concatenate((np.zeros(10), np.ones(10))))
    expected_locus_neutral = list(np.zeros(40))
    expected_locus_behaviour = list(np.array([0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1,
                                              1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0]))
    expected_phenotype = list(np.array([0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0]))
    assert survivors == expected_survivors
    assert group_0 == group_1 == expected_group
    assert locus_neutral_0 == locus_neutral_1 == expected_locus_neutral
    assert locus_behaviour_0 == locus_behaviour_1 == expected_locus_behaviour
    assert phenotype_0 == phenotype_1 == expected_phenotype


@pytest.mark.parametrize('general_configuration, expected_deaths', [
    ([0, 100, 20, 0, 0, 1, 0, None, 1, 0, 1, 3, 10], 0),
    ([0, 100, 20, 0, 0, 1, 0, None, 1, 0, 0.5, 3, 10], 10),
    ([0, 100, 20, 0, 0, 1, 0, None, 1, 0, 0, 3, 10], 20)
])
def test_selection_event_bag(general_configuration, expected_deaths, ba_dom_model_configuration):
    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    initial_inds_per_group = []
    for group in simulation.groups:
        initial_inds_per_group.append(len(group))
    simulation.selection_event()
    survivors_per_group = []
    for group_i in range(len(simulation.groups)):
        survivors = initial_inds_per_group[group_i] - len(simulation.groups[group_i])
        survivors_per_group.append(survivors)
    result_deaths = np.round(np.mean(survivors_per_group))
    assert result_deaths == expected_deaths


# Generates an Individual object with the configured immigrant genotype
@pytest.mark.parametrize('general_configuration, model_configuration, expected_result', [
    ([0, 1, 20, 0, 0, 0, 1, 'altruistic, neutral', 1, 0, 1, 3, 10],
     {'module': {'name': 'blind_altruism'},
      'behaviour': {'alleles': 'selfish > altruistic',
                    'initial_frequencies': '0.5, 0.5',
                    'locus_size': '0',
                    'mutation_rate': '0',
                    'recombination_rate': '0'},
      'neutral': {'alleles': 'neutral > neutral',
                  'initial_frequencies': '0.5, 0.5',
                  'locus_size': '0',
                  'mutation_rate': '0',
                  'recombination_rate': '0'}},
     {"[['selfish', 'selfish'], ['neutral', 'neutral']]": 0,
      "[['selfish', 'altruistic'], ['neutral', 'neutral']]": 0,
      "[['altruistic', 'selfish'], ['neutral', 'neutral']]": 0,
      "[['altruistic', 'altruistic'], ['neutral', 'neutral']]": 1}
     ),
    ([0, 1, 20, 0, 0, 0, 1, 'selfish, neutral', 1, 0, 1, 3, 10],
     {'module': {'name': 'blind_altruism'},
      'behaviour': {'alleles': 'selfish > altruistic',
                    'initial_frequencies': '0.5, 0.5',
                    'locus_size': '0',
                    'mutation_rate': '0',
                    'recombination_rate': '0'},
      'neutral': {'alleles': 'neutral > neutral',
                  'initial_frequencies': '0.5, 0.5',
                  'locus_size': '0',
                  'mutation_rate': '0',
                  'recombination_rate': '0'}},
     {"[['selfish', 'selfish'], ['neutral', 'neutral']]": 1,
      "[['selfish', 'altruistic'], ['neutral', 'neutral']]": 0,
      "[['altruistic', 'selfish'], ['neutral', 'neutral']]": 0,
      "[['altruistic', 'altruistic'], ['neutral', 'neutral']]": 0}
     )
])
def test_generate_immigrant_bag(general_configuration, model_configuration, expected_result):
    # random.seed(496296)
    simulation = Simulation(*general_configuration, model_configuration)
    replicas = 100
    genotypes_dictionary = {"[['selfish', 'selfish'], ['neutral', 'neutral']]": 0,
                            "[['selfish', 'altruistic'], ['neutral', 'neutral']]": 0,
                            "[['altruistic', 'selfish'], ['neutral', 'neutral']]": 0,
                            "[['altruistic', 'altruistic'], ['neutral', 'neutral']]": 0}
    for i in range(replicas):
        genotype = str(simulation.generate_immigrant().genotype)
        genotypes_dictionary[genotype] += 1
    # Transform counts to proportions
    genotypes_dictionary = {k: v / replicas for _ in (sum(genotypes_dictionary.values()),)
                            for k, v in genotypes_dictionary.items()}
    assert genotypes_dictionary == expected_result


# The proportion of the population configured will emigrate out of the population
@pytest.mark.parametrize('general_configuration', [
    ([0, 1, 20, 0, 0, 1, 0, None, 1, 0, 1, 3, 10]),
    ([0, 1, 20, 0, 0, 0.5, 0, None, 1, 0, 1, 3, 10]),
    ([0, 1, 20, 0, 0, 0.1, 0, None, 1, 0, 1, 3, 10]),
    ([0, 1, 20, 0, 0, 0, 0, None, 1, 0, 1, 3, 10])
])
def test_emigration_bag(general_configuration, ba_dom_model_configuration):
    # random.seed(588786)
    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    initial_population_size = 0
    for group in simulation.groups:
        initial_population_size += len(group)

    simulation.migration()

    result_population_size = 0
    for group in simulation.groups:
        result_population_size += len(group)

    expected_population_size = initial_population_size - initial_population_size * general_configuration[5]
    assert result_population_size == expected_population_size


# The proportion of the population configured will be immigrants with the correct phenotype
@pytest.mark.parametrize('general_configuration', [
    ([0, 1, 20, 0, 0, 0, 1, 'altruistic, neutral', 1, 0, 1, 3, 10]),
    ([0, 1, 20, 0, 0, 0, 0.5, 'selfish, neutral', 1, 0, 1, 3, 10]),
    ([0, 1, 20, 0, 0, 0, 0.1, 'altruistic, neutral', 1, 0, 1, 3, 10]),
    ([0, 1, 20, 0, 0, 0, 0, 'selfish, neutral', 1, 0, 1, 3, 10])
])
def test_immigration_bag(general_configuration, ba_dom_model_configuration):
    # random.seed(313951)
    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    initial_phenotypes = {"['selfish', 'neutral']": 0,
                          "['altruistic', 'neutral']": 0}
    for group_i in range(len(simulation.groups)):
        simulation.groups[group_i] = simulation.groups[group_i][0:int(len(simulation.groups[group_i]) / 2)]
        for ind in simulation.groups[group_i]:
            initial_phenotypes[str(ind.phenotype)] += 1
    current_population_size = 0
    for count in initial_phenotypes.values():
        current_population_size += count
    full_population_size = general_configuration[2]
    immigrant_proportion = general_configuration[6]
    immigrant_phenotype = general_configuration[7].replace(' ', '').split(',')
    immigrants = min(round(full_population_size * immigrant_proportion),
                     full_population_size - current_population_size)

    expected_phenotypes = initial_phenotypes
    expected_phenotypes[f"{immigrant_phenotype}"] += immigrants

    simulation.migration()
    result_phenotypes = {"['selfish', 'neutral']": 0,
                         "['altruistic', 'neutral']": 0}
    for group in simulation.groups:
        for ind in group:
            result_phenotypes[str(ind.phenotype)] += 1
    assert result_phenotypes == expected_phenotypes


@pytest.mark.parametrize('sire_genotype, dam_genotype, expected_genotype', [
    ([['altruistic', 'altruistic'], ['neutral', 'neutral']],
     [['altruistic', 'altruistic'], ['neutral', 'neutral']],
     [['altruistic', 'altruistic'], ['neutral', 'neutral']]),

    ([['altruistic', 'altruistic'], ['neutral', 'neutral']],
     [['selfish', 'selfish'], ['neutral', 'neutral']],
     [['altruistic', 'selfish'], ['neutral', 'neutral']]),

    ([['altruistic', 'selfish'], ['neutral', 'neutral']],
     [['altruistic', 'selfish'], ['neutral', 'neutral']],
     [['altruistic', 'selfish'], ['neutral', 'neutral']]),

    ([['selfish', 'selfish'], ['neutral', 'neutral']],
     [['selfish', 'selfish'], ['neutral', 'neutral']],
     [['selfish', 'selfish'], ['neutral', 'neutral']])
])
def test_generate_offspring_genome_bag(sire_genotype, dam_genotype, expected_genotype,
                                       base_general_configuration, ba_dom_model_configuration):
    np.random.seed(221317)
    random.seed(221317)
    simulation = Simulation(*base_general_configuration, ba_dom_model_configuration)
    sire = Individual(simulation)
    sire.genotype = sire_genotype
    sire.generate_genome()
    dam = Individual(simulation)
    dam.genotype = dam_genotype
    dam.generate_genome()

    sire_chromosomes = [[chromosome for chromosome in locus.chromosomes] for locus in sire.genome.loci]
    dam_chromosomes = [[chromosome for chromosome in locus.chromosomes] for locus in dam.genome.loci]
    reproducers_chromosomes = [sire_chromosomes, dam_chromosomes]

    descendant = Individual(simulation)
    simulation.generate_offspring_genome([sire, dam], descendant)
    chromosomes_origin = []
    for locus in descendant.genome.loci:
        for chromosome in locus.chromosomes:
            if any(chromosome in locus for locus in reproducers_chromosomes[0]):
                print(chromosome, reproducers_chromosomes[0])
                chromosomes_origin.append(0)
            elif any(chromosome in locus for locus in reproducers_chromosomes[1]):
                chromosomes_origin.append(1)
    loci_origin = [(chromosomes_origin[i] + chromosomes_origin[i+1]) / 2 for i in range(0, len(chromosomes_origin), 2)]
    assert descendant.genotype == expected_genotype
    assert loci_origin == [0.5, 0.5]


@pytest.mark.parametrize('sire_id, sire_ancestry, dam_id, dam_ancestry, expected_ancestry', [
    (1, [[0, 0], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
     2, [[0, 0], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
     [[1, 2], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]]),
    (1, [[3, 4], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
     2, [[3, 4], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
     [[1, 2], [3, 4, 3, 4], [0, 0, 0, 0, 0, 0, 0, 0]]),
    (1, [[3, 0], [5, 6, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
     2, [[4, 7], [0, 0, 8, 9], [0, 0, 0, 0, 0, 0, 0, 0]],
     [[1, 2], [3, 0, 4, 7], [5, 6, 0, 0, 0, 0, 8, 9]]),
])
def test_generate_offspring_ancestry_bag(sire_id, sire_ancestry, dam_id, dam_ancestry, expected_ancestry,
                                         base_general_configuration, ba_dom_model_configuration):
    simulation = Simulation(*base_general_configuration, ba_dom_model_configuration)
    sire = Individual(simulation)
    sire.ancestry = sire_ancestry
    sire.id = sire_id
    dam = Individual(simulation)
    dam.ancestry = dam_ancestry
    dam.id = dam_id

    descendant = Individual(simulation)
    simulation.generate_offspring_ancestry([sire, dam], descendant)
    assert descendant.ancestry == expected_ancestry


def test_discard_old_individuals_bag(ba_dom_model_configuration):
    general_configuration = [0, 1, 5000, 0, 0, 0, 0, None, 20, 2, 1, 3, 10]
    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    gen_of_death = []
    for i in range(80):
        start_inds = len(simulation.groups[0])
        simulation.groups = simulation.discard_old_individuals()
        simulation.group_exchange()
        final_inds = len(simulation.groups[0])
        simulation.generation += 1
        for j in range(start_inds - final_inds):
            gen_of_death.append(simulation.current_generation)
    mean = np.mean(gen_of_death)
    sd = np.std(gen_of_death)
    assert mean == pytest.approx(20, abs=0.1)
    assert sd == pytest.approx(2, abs=0.1)


def test_reproduce_bag(ba_dom_model_configuration):
    # np.random.seed(310145)
    random.seed(320175)
    general_configuration = [0, 1, 10, 0, 0, 0, 0, None, 10, 0, 0.5, 3, 10]
    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    simulation.selection_event()
    # Last ind will die of old age but will leave offspring
    simulation.groups[0][-1].life_expectancy = 1
    simulation.reproduce()

    reproducers_ids = []
    for newborn in simulation.groups[0][5:]:
        reproducers_ids.append(newborn.ancestry[0])

    individuals = []
    for ind in simulation.groups[0]:
        individuals.append(ind.id)

    assert len(simulation.groups[0]) == 10
    assert reproducers_ids == [[4, 10], [2, 7], [7, 2], [9, 3], [10, 7]]
    assert individuals == [2, 3, 4, 7, 9, 11, 12, 13, 14, 15]


# The proportion of the population configured will emigrate out of the population
@pytest.mark.parametrize('general_configuration', [
    ([0, 5, 20, 5, 0.25, 0, 0, None, 1, 0, 1, 3, 10])
])
def test_group_exchange_bag(general_configuration, ba_dom_model_configuration):
    np.random.seed(162497)
    random.seed(162497)
    expected_groups = [[34, 33, 54, 76, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 16, 17, 18, 19, 21, 22, 23],
                       [6, 65, 75, 103, 101, 105, 24, 25, 26, 27, 28, 29, 30, 32, 36, 37, 39, 40, 41, 42, 43, 45, 46,
                        47, 49, 50],
                       [15, 13, 44, 38, 78, 80, 92, 52, 53, 55, 56, 57, 58, 59, 61, 62, 63, 64, 66, 68, 69, 70],
                       [7, 35, 48, 51, 67, 71, 72, 73, 74, 77, 79, 81, 82, 83, 84, 85, 86, 87, 88, 90, 91],
                       [14, 20, 31, 60, 89, 93, 94, 95, 96, 97, 98, 99, 100, 102, 104, 106, 107, 108]]

    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    initial_population_size = 0
    for group in simulation.groups:
        initial_population_size += len(group)
    simulation.group_exchange()
    final_population_size = 0
    for group in simulation.groups:
        final_population_size += len(group)
    result_groups = []
    for group in simulation.groups:
        group_ids = []
        for ind in group:
            group_ids.append(ind.id)
        result_groups.append(group_ids)

    flat_groups = [num for sublist in simulation.groups for num in sublist]
    id_counts = {}
    not_repeated_individuals = True
    for elem in flat_groups:
        if elem not in id_counts.keys():
            id_counts[elem] = 1
        else:
            not_repeated_individuals = False
            break
    assert result_groups == expected_groups
    assert not_repeated_individuals
    assert initial_population_size == final_population_size


def test_generations_bag(ba_dom_model_configuration):
    general_configuration = [9, 1, 50, 0, 0, 0, 0, None, 1, 0, 1, 3, 10]
    simulation = Simulation(*general_configuration, ba_dom_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    for i in range(simulation.generations):
        simulation.pass_generation()
    assert simulation.current_generation == 10


def test_save_haplotypes(ba_haplotypes_model_configuration):
    # np.random.seed(245079)
    # random.seed(245079)
    general_configuration = [2, 1, 10, 0, 0, 0, 0, None, 1, 0, 1, 3, 10]
    simulation = Simulation(*general_configuration, ba_haplotypes_model_configuration)
    simulation.populate_groups()
    simulation.save_generation_data()
    for i in range(3):
        simulation.pass_generation()
    result_haplotypes = simulation.save_haplotypes()
    haplotypes_in_result = True
    for ind in simulation.groups[0]:
        for locus, locus_index in zip(ind.genome.loci, range(len(ind.genome.loci))):
            for chromosome in locus.chromosomes:
                if tuple(chromosome.snvs_to_sequence(locus.locus_size)) not in result_haplotypes[locus_index]:
                    haplotypes_in_result = False
                    break
            if not haplotypes_in_result:
                break
        if not haplotypes_in_result:
            break
    assert haplotypes_in_result