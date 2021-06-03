import functools
import itertools
import sympy
from sympy.printing.latex import latex
import drawSvg as draw
import latextools

VERBOSE = False


def _disp(svg, msg):
    '''Show rendering progress when VERBOSE is True.'''
    if not VERBOSE: return svg
    try:
        from IPython.display import display
    except ImportError:
        display = print
    class DispWrap:
        def _repr_svg_(self): return d._repr_svg_()
        def __repr__(self): return msg
    d = draw.Drawing(50, 20, origin='center', displayInline=False)
    d.draw(svg, center=True)
    display(DispWrap())
    return svg

@functools.lru_cache(maxsize=None)
def render_cache(latex):
    return _disp(latextools.render_snippet(
            latex,
            latextools.pkg.qcircuit,
            latextools.pkg.xcolor,
            commands=[latextools.cmd.all_math],
            pad=1,
        ).as_svg(),
        msg=f'Rendered LaTeX element: {latex}')

def sympy_to_math_mode(sym):
    '''Returns the latex math code (without surrounding $) for the sympy symbol.
    '''
    return latex(sym, mode='plain', fold_frac_powers=True)

def render_label(amp_sym, label):
    '''Render preset sympy expressions as nice LaTeX equations.'''
    presets = {
        sympy.sympify(0): '0',
        sympy.sympify(1): '1',
        sympy.sympify(-1): '-1',
    }
    if amp_sym in presets:
        amp_latex = presets[amp_sym]
    else:
        # Generate latex for any ±1 / sqrt(2) ** x
        amp_latex = ''
        give_up = False
        amp_sym_orig = amp_sym
        if abs(amp_sym) == -amp_sym:
            amp_latex += '-'
            amp_sym = -amp_sym
        elif abs(amp_sym) == amp_sym:
            pass
        else:
            give_up = True
        if not give_up:
            x = 0
            sqrt2 = sympy.sqrt(2)
            while amp_sym < 1:
                amp_sym = amp_sym * sqrt2
                x += 1
            if amp_sym != 1:
                give_up = True
            else:
                inner = f'{2**(x//2)}' if x // 2 > 0 else ''
                inner += r'\sqrt{2}' if x % 2 == 1 else ''
                amp_latex += fr'\frac1{{{inner}}}'
        if give_up:
            # The expression displayed may not be simplified in the desired way.
            amp_latex = sympy_to_math_mode(amp_sym_orig)
    return render_cache(fr'${amp_latex}\ket{{{label}}}$')


class Diagram:
    def __init__(self, n_qubits, init_state=None,
                 w_time = 120,
                 h_state = 40,
                 font = 12,
                 gate_font = 16,
                 ws_label = 6,
                 arrow_space = 1):
        if arrow_space > ws_label/2:
            arrow_space = ws_label/2
        self.w_time = w_time
        self.h_state = h_state
        self.font = font
        self.gate_font = gate_font
        self.w_label = self.font * ws_label
        self.arrow_off = self.w_label/2 * arrow_space

        self.d = draw.Group()
        self.arrows = {}
        self.possible_states = [
            ''.join(map(str, qs[::-1]))
            for qs in itertools.product(range(2), repeat=n_qubits)
        ]
        self.num_states = len(self.possible_states)

        if init_state is None:
            init_state = {'0'*n_qubits: 1}
        self.state_sequence = [init_state]
        self.draw_states()

    def draw(self):
        w = (len(self.state_sequence)-1) * self.w_time + self.w_label - self.font*0.5
        h = (self.num_states-1) * self.h_state + self.font*2 + self.gate_font*3
        x = -self.w_label/2 + self.font
        y = -(self.num_states-1)/2 * self.h_state - self.font*1.5
        d = draw.Drawing(w, h, origin=(x, y), displayInline=False)
        d.append(self.d)
        return d
    def _repr_html_(self):
        return self.draw()._repr_html_()
    def _repr_svg_(self):
        return self.draw()._repr_svg_()

    def state_xy(self, key, time):
        state_idx = self.possible_states.index(key)
        x = time * self.w_time
        y = ((self.num_states-1)/2 - state_idx) * self.h_state
        return x, y

    def transition_text(self, g, start_time, label):
        x = (start_time+0.5) * self.w_time
        y = (self.num_states-1)/2 * self.h_state + self.font/2+self.gate_font*3/2
        g.draw(render_cache(fr'${label}$'),
               x=x, y=y, scale=self.gate_font/12, center=True)

    def state_text(self, g, time, key, amp=1):
        state_idx = self.possible_states.index(key)
        x, y = self.state_xy(key, time)
        g.draw(render_label(sympy.sympify(amp), key),
               x=x+self.w_label/2-self.font*0.2, y=y, scale=self.font/12, center=True, text_anchor='end')
        if abs(float(amp)) < 1e-8:
            # Draw red X over it
            ys = self.font/2*1.4
            xs = self.w_label/2*0.7
            xf = self.font
            g.append(draw.Line(x+xf-xs, y-ys, x+xf+xs, y+ys, stroke='red', stroke_width=1))
            g.append(draw.Line(x+xf-xs, y+ys, x+xf+xs, y-ys, stroke='red', stroke_width=1))

    def make_arrow(self, color):
        key = color
        if key in self.arrows:
            return self.arrows[key]
        arrow = draw.Marker(-0.1, -0.5, 1.1, 0.5, scale=4)
        arrow.append(draw.Lines(1, -0.5, 1, 0.5, 0, 0, fill=color, close=True))
        self.arrows[key] = arrow
        return arrow

    def straight_arrow(self, g, color, *xy_list, width=1):
        rev_xy = xy_list[::-1]
        rev_xy = [rev_xy[i+1-2*(i%2)] for i in range(len(rev_xy))]
        w = 3 * width
        g.append(draw.Line(*rev_xy,
                 stroke=color, stroke_width=w, fill='none',
                 # Pull the line behind the arrow
                 stroke_dasharray=f'0 {w*4/2} 1000000',
                 marker_start=self.make_arrow(color)))

    def gate_arrow(self, g, time1, key1, key2, amp=1):
        w = float(abs(amp))
        x1, y1 = self.state_xy(key1, time1)
        x2, y2 = self.state_xy(key2, time1+1)
        x1 += self.arrow_off
        x2 -= self.arrow_off
        xx1 = x1 + self.w_label/2 - self.arrow_off
        xx2 = x2 - self.w_label/2 + self.arrow_off
        yy1 = y1 + (y2-y1)*(xx1-x1)/(x2-x1)
        yy2 = y2 - (y2-y1)*(x2-xx2)/(x2-x1)
        color = '#26f'
        if abs(float(amp) - abs(float(amp))) >= 1e-8:
            color = '#e70'
        self.straight_arrow(g, color, xx1, yy1, xx2, yy2, width=w)

    def draw_states(self):
        t = len(self.state_sequence)-1
        for key, amp in self.state_sequence[-1].items():
            self.state_text(self.d, t, key, amp=amp)

    def add_states(self, new_state):
        self.state_sequence.append(new_state)
        self.draw_states()
        clean_state = {
            key: amp
            for key, amp in new_state.items()
            if abs(float(amp)) >= 1e-8
        }
        self.state_sequence[-1] = clean_state

    def perform_h(self, q_i, *, pre_latex=f'', name='H'):
        new_state = {}
        t = len(self.state_sequence)-1
        for key, amp in self.state_sequence[-1].items():
            is_one = key[q_i] == '1'
            digits = list(key)
            digits[q_i] = '0'
            zero = ''.join(digits)
            digits[q_i] = '1'
            one = ''.join(digits)
            zero_amp = 1/sympy.sqrt(2)
            one_amp = -zero_amp if is_one else zero_amp
            self.gate_arrow(self.d, t, key, zero, amp=zero_amp)
            self.gate_arrow(self.d, t, key, one, amp=one_amp)
            if zero not in new_state: new_state[zero] = 0
            if one not in new_state: new_state[one] = 0
            new_state[zero] += amp*zero_amp
            new_state[one] += amp*one_amp
        self.transition_text(self.d, t, f'{pre_latex}{name}_{q_i}')
        self.add_states(new_state)

    def perform_cnot(self, qi1, qi2, *, pre_latex=f'', name='CNOT'):
        new_state = {}
        t = len(self.state_sequence)-1
        for key, amp in self.state_sequence[-1].items():
            is_one = key[qi1] == '1'
            is_targ_one = key[qi2] == '1'
            digits = list(key)
            if is_one:
                digits[qi2] = '01'[not is_targ_one]
            new_key = ''.join(digits)
            self.gate_arrow(self.d, t, key, new_key, amp=1)
            if new_key not in new_state: new_state[new_key] = 0
            new_state[new_key] += amp
        self.transition_text(self.d, t, f'{pre_latex}{name}_{{{qi1}{qi2}}}')
        self.add_states(new_state)

    def perform_z(self, q_i, *, pre_latex=f'', name='Z'):
        new_state = {}
        t = len(self.state_sequence)-1
        for key, amp in self.state_sequence[-1].items():
            is_one = key[q_i] == '1'
            new_amp = -amp if is_one else amp
            self.gate_arrow(self.d, t, key, key, amp=new_amp/amp)
            if key not in new_state: new_state[key] = 0
            new_state[key] += new_amp
        self.transition_text(self.d, t, f'{pre_latex}{name}_{{{q_i}}}')
        self.add_states(new_state)

    def perform_x(self, q_i, *, pre_latex=f'', name='X'):
        new_state = {}
        t = len(self.state_sequence)-1
        for key, amp in self.state_sequence[-1].items():
            is_one = key[q_i] == '1'
            digits = list(key)
            digits[q_i] = '01'[not is_one]
            new_key = ''.join(digits)
            self.gate_arrow(self.d, t, key, new_key, amp=1)
            if new_key not in new_state:
                new_state[new_key] = 0
            new_state[new_key] += amp
        self.transition_text(self.d, t, f'{pre_latex}{name}_{{{q_i}}}')
        self.add_states(new_state)
