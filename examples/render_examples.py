#!/usr/bin/env python3

from feynman_path import command


print('\nRendering interference')
#$ feynman_path interference 2 h0 cnot0,1 z1 h0 h1 cnot1,0 h1
# Save all formats and the corresponding circuit diagram
for circuit in [False, True]:
    command.main('interference',
                 2,
                 'h0 cnot0,1 z1 h0 h1 cnot1,0 h1'.split(),
                 svg=True,
                 png=True,
                 pdf=True,
                 scale=3,
                 sequence=False,
                 circuit=circuit)


print('\nRendering no-interference')
#$ feynman_path no-interference 3 h0 cnot0,1 z1 cnot1,2 h0 h1 cnot1,0 h1
# Save the circuit diagram
command.main('no-interference',
             3,
             'h0 cnot0,1 z1 cnot1,2 h0 h1 cnot1,0 h1'.split(),
             svg=True,
             png=True,
             pdf=True,
             scale=3,
             sequence=False,
             circuit=True)
# Manually create the path diagram so we can highlight CNOT_12 in red
f = command.draw_diagram(3, [])
f.perform_h(0)
f.perform_cnot(0, 1)
f.perform_z(1)
f.perform_cnot(1, 2, pre_latex=r'\color{red!80!black}')
f.perform_h(0)
f.perform_h(1)
f.perform_cnot(1, 0)
f.perform_h(1)
command.save_formats_from_svg(f.draw(), 'no-interference',
                              svg=True, png=True, pdf=True, scale=3)


print('\nRendering entanglement')
#$ feynman_path no-entanglement 2 h0 cnot0,1 h0 h1
# Save all formats and the corresponding circuit diagram
for circuit in [False, True]:
    command.main('entanglement',
                 2,
                 'h0 cnot0,1 h0 h1'.split(),
                 svg=True,
                 png=True,
                 pdf=True,
                 scale=3,
                 sequence=False,
                 circuit=circuit)


print('\nRendering no-entanglement')
#$ feynman_path no-entanglement 2 h0 h1 cnot0,1 h0 h1
# Save all formats and the corresponding circuit diagram
for circuit in [False, True]:
    command.main('no-entanglement',
                 2,
                 'h0 h1 cnot0,1 h0 h1'.split(),
                 svg=True,
                 png=True,
                 pdf=True,
                 scale=3,
                 sequence=False,
                 circuit=circuit)
