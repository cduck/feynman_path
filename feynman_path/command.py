import argparse
import latextools

from . import diagram


def parse_gate(gate_str):
    name = gate_str.translate({ord(digit): '-' for digit in '0123456789'}
                             ).split('-')[0]
    args = tuple(int(arg) for arg in gate_str[len(name):].split(','))
    return name, args

def draw_diagram(n_qubits, gates):
    '''Draw a path sum diagram'''
    ws_label = 4+0.55*n_qubits
    f = diagram.Diagram(
            n_qubits,
            font=12, ws_label=ws_label, w_time=60+ws_label*12
        )

    for gate in gates:
        name, args = parse_gate(gate)
        getattr(f, f'perform_{name}')(*args)

    return f

def draw_circuit_pdf(n_qubits, gates):
    '''Draw a basic circuit diagram using qcircuit in LaTeX'''
    lines = [fr'\lstick{{q_{{{i}}}}}' for i in range(n_qubits)]
    for gate in gates:
        name, args = parse_gate(gate)
        if len(args) == 1:
            name = name[:1].upper() + name[1:]
            for i in range(n_qubits):
                if i == args[0]:
                    lines[i] += fr' & \gate{{{name}}}'
                else:
                    lines[i] += fr' & \qw'
        elif len(args) == 2 and name.upper().startswith('C'):
            name = name[:1].upper() + name[1:]
            targ = (r' & \targ' if name.upper() == 'CNOT'
                             else fr' & \gate{{{name}}}')
            ctrl_len = args[1] - args[0]
            for i in range(n_qubits):
                if i == args[0]:
                    lines[i] += fr' & \ctrl{{{ctrl_len}}}'
                elif i == args[1]:
                    lines[i] += targ
                else:
                    lines[i] += fr' & \qw'
        else:
            raise NotImplementedError(
                    f'Unsupported circuit diagram gate "{name}"')
    for i in range(n_qubits):
        lines[i] += r' & \qw \\'

    pdf = latextools.render_qcircuit(
            '\n'.join(lines),
            lpad=22, rpad=22, tpad=6, bpad=6, r=0.5, c=1,
            const_row=True, const_col=True, const_size=True)
    return pdf

def save_formats_from_pdf(p, name, msg='', svg=False, png=False, pdf=False,
                          scale=1):
    if pdf:
        p.save(f'{name}.pdf')
        print(f'Saved "{name}.pdf"{msg}')
    if svg or png:
        d = p.as_svg().as_drawing()
    if svg:
        d.saveSvg(f'{name}.svg')
        print(f'Saved "{name}.svg"{msg}')
    if png:
        d.setPixelScale(scale)
        d.savePng(f'{name}.png')
        print(f'Saved "{name}.png"{msg}')

def save_formats_from_svg(d, name, msg='', svg=False, png=False, pdf=False,
                          scale=1):
    if pdf:
        p = latextools.svg_to_pdf(d)
        p.save(f'{name}.pdf')
        print(f'Saved "{name}.pdf"{msg}')
    if svg:
        d.saveSvg(f'{name}.svg')
        print(f'Saved "{name}.svg"{msg}')
    if png:
        d.setPixelScale(scale)
        d.savePng(f'{name}.png')
        print(f'Saved "{name}.png"{msg}')

def main(name, n_qubits, gates, svg=False, png=False, pdf=False, sequence=False,
         circuit=False, scale=1):
    gates_sequence = [gates]
    if sequence:
        gates_sequence = [gates[:i] for i in range(len(gates)+1)]

    for i, gates in enumerate(gates_sequence):
        name_seq = f'{name}-{i:02}' if sequence else name
        gates_str = ' '.join(gates)
        if circuit:
            name_seq += '-circuit'
            # Draw a circuit diagram instead
            p = draw_circuit_pdf(n_qubits, gates)
            save_formats_from_pdf(
                    p, name_seq, msg=f' with gate sequence "{gates_str}"',
                    svg=svg, png=png, pdf=pdf, scale=scale
                )
        else:
            # Draw a path diagram
            d = draw_diagram(n_qubits, gates).draw()
            save_formats_from_svg(
                    d, name_seq, msg=f' with gate sequence "{gates_str}"',
                    svg=svg, png=png, pdf=pdf, scale=scale
                )

def run_from_command_line():
    parser = argparse.ArgumentParser(
        description='Renders a Feynman path sum diagram for a sequence of '
                    'quantum gates.')
    parser.add_argument('name', type=str, help=
        'The file name to save (excluding file extension)')
    parser.add_argument('n_qubits', type=int, help=
        'The number of qubits in the quantum circuit')
    parser.add_argument('gate', type=str, nargs='+', help=
        'List of gates to apply (e.g. h0 z1 cnot0,1)')
    parser.add_argument('--svg', action='store_true', help=
        'Save diagram as an SVG image (default)')
    parser.add_argument('--png', action='store_true', help=
        'Save diagram as a PNG image')
    parser.add_argument('--pdf', action='store_true', help=
        'Save diagram as a PDF document')
    parser.add_argument('--sequence', action='store_true', help=
        'Save a sequence of images that build up the diagram from left to right as <name>-nn.svg/png/pdf')
    parser.add_argument('--circuit', action='store_true', help=
        'Save a standard quantum circuit diagram named <name>-circuit.svg/png/pdf instead of a Feynman path diagram')
    parser.add_argument('--scale', type=float, default=1, help=
        'Scales the resolution of the diagram when saved as a PNG')
    parser.add_argument('--verbose', action='store_true', help=
        'Print extra progress information')

    args = parser.parse_args()
    # Enable verbose
    if args.verbose:
        diagram.VERBOSE = True
    # If no output formats are selected, default to SVG
    svg = args.svg or (not args.png and not args.pdf)

    main(name=args.name, n_qubits=args.n_qubits, gates=args.gate, svg=svg,
         png=args.png, pdf=args.pdf, sequence=args.sequence,
         circuit=args.circuit, scale=args.scale)
