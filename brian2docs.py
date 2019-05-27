import re
import sympy
import os.path
import subprocess
from graphviz import Digraph
from brian2tools import brian_plot
from matplotlib import pyplot as pp
from brian2.parsing.sympytools import str_to_sympy
from jinja2 import Environment, FileSystemLoader
from brian2 import Synapses, NeuronGroup, SpatialNeuron, CodeRunner, Subgroup, PoissonInput, Quantity, Cylinder, Soma
from brian2.monitors import SpikeMonitor, StateMonitor, PopulationRateMonitor
import warnings
import matplotlib.pyplot as plt
import re
from collections import defaultdict


def replace_underscore(x):
    return '\\texttt{' + x.replace('_', '\\_') + '}'


def convert_code_to_latex_listing(code):
    '''
    convert abstract_code for example in CodeRunner and Synapse prepost to latex style code listing
    '''
    l = code.split('\n')
    l = [i.strip() for i in l]
    begin_listing = '\n\\begin{lstlisting}\n'
    eqs = begin_listing + '\n\n'.join(l) + '\n\\end{lstlisting}\n'

    return eqs


def generate_PoissonInput_latex(PI):
    code = convert_code_to_latex_listing(PI.abstract_code)

    PI_string = []
    PI_string.append('\\section{PoissonInput ' + replace_underscore(PI.name) + '}')
    PI_string.append('\\begin{itemize}')
    PI_string.append('\\item \\textbf{target:}')
    PI_string.append(replace_underscore(PI._group.name))
    PI_string.append('\\item \\textbf{target start and stop:}')
    PI_string.append('start from ' + str(PI._group.start) + ', stops at ' + str(PI._group.stop))
    PI_string.append('\\item \\textbf{Target Variable and Weight:}')
    PI_string.append(code)
    PI_string.append('\\item \\textbf{N:}')
    PI_string.append(str(PI.N))
    PI_string.append('\\item \\textbf{Rate:}')
    PI_string.append('$' + PI.rate.in_best_unit() + '$')
    PI_string.append('\\item \\textbf{When:}')
    PI_string.append(PI.when)
    PI_string.append('\\item \\textbf{Order:}')
    PI_string.append(str(PI.order))
    PI_string.append('\\end{itemize}')

    return '\n'.join(PI_string)


def generate_CodeRunner_latex(CR):
    '''
    generate latex code for coderunner object created by 'run_regularly' function of NeuronGroup
    '''
    code = convert_code_to_latex_listing(CR.abstract_code)
    dt = CR.clock.dt.in_best_unit()

    CR_string = []
    CR_string.append('\\section{run\\texttt{\\_}regularly ' + replace_underscore(CR.name) + '}')
    CR_string.append('\\begin{itemize}')
    CR_string.append('\\item \\textbf{Abstract Code:}')
    CR_string.append(code)
    CR_string.append('\\item \\textbf{Clock dt:} $' + dt + '$')
    CR_string.append('\\end{itemize}')

    return '\n'.join(CR_string)


def generate_ng_latex(NG, log_dict):
    '''
    NG: NeuronGroup

    generate a string containing latex format presentation of input NeuronGroup
    '''

    def add_event_to_text(event):
        if event == 'spike':
            event_header = 'Spiking\:Behaviour'
            event_condition = 'Threshold condition'
            event_code = 'Reset statement(s)'
        else:
            event_header = 'Event %s' % replace_underscore(event)
            event_condition = 'Event Condition'
            event_code = 'Executed Statement(s)'
        condition = NG.events[event]
        text.append('\\textbf{%s:}\n\\begin{itemize}' % event_header)
        text.append(r'\item \textit{%s:}' % event_condition)
        text.append('\\begin{lstlisting}\n' + str(condition) + '\n\\end{lstlisting}')
        statements = NG.event_codes.get(event, None)
        if statements is not None:
            text.append(r'\item \textit{%s:}' % event_code)
            text.append('\\begin{lstlisting}\n' + str(statements) + '\n\\end{lstlisting}')
        text.append('\end{itemize}')

    def generate_SpatialNeuron_latex(NG):

        text = []
        text.append('\\item\\textbf{Cm:}')
        text.append('$' + NG.Cm[0].in_best_unit() + '$')
        text.append('\\item\\textbf{Ri:}')
        text.append('$' + str(NG.Ri.variable.get_value()[0]) + '\:' + NG.Ri.unit.latexname + '$')

        if NG.morphology is not None:
            morpho = NG.morphology
            pic_path = 'tmp/' + NG.name + '.pdf'
            plt.close()
            brian_plot(morpho)
            pp.savefig(pic_path)
            NG_name = replace_underscore(NG.name)

            text.append('\\item \\textbf{Morphology:}')
            text.append('\\begin{itemize}')

            text.append('\\item\\textbf{Morphology graph of ' + NG_name + ':}')
            text.append('\\begin{center}')
            text.append('\\includegraphics[width=\\textwidth]{' + pic_path + '}')
            text.append('\\end{center}')

            text.append('\\item \\textbf{class:}' + type(morpho).__name__)
            if isinstance(morpho, Cylinder):
                text.append('\\item \\textbf{diameter:}')
                text.append('$' + morpho.diameter[0].in_best_unit() + '$')
                text.append('\\item \\textbf{n:}')
                text.append(str(morpho.n))
                text.append('\\item \\textbf{length:}')
                text.append('${length!r}$'.format(length=sum(morpho._length)))
            elif isinstance(morpho, Soma):
                text.append('\\item \\textbf{diameter:}')
                text.append('$' + morpho.diameter[0].in_best_unit() + '$')

            text.append('\\end{itemize}')

        return '\n'.join(text)

    NG_name = replace_underscore(NG.name)
    text = ['\n\\section{NeuronGroup %s}\n' % (NG_name), r'NeuronGroup "%s" with %d neurons.\\\\' % (NG_name, NG._N)]
    text.append('\\begin{itemize}')
    text.append('\\item')
    text.append(r'\textbf{Model:} \\ ')
    text.append(sympy.latex(NG.equations))

    if 'spike' in NG.events:
        text.append('\\item\n')
        add_event_to_text('spike')
    for event in NG.events:
        if event != 'spike':
            text.append('\\item\n')
            add_event_to_text(event)

    text.append('\\item')
    text.append('\\textbf{Refractory:}\\begin{lstlisting}')
    if isinstance(NG._refractory, bool):
        if NG._refractory:
            text.append('True')
        else:
            text.append('False')
    elif isinstance(NG._refractory, Quantity):
        text.append(NG._refractory.in_best_unit())

    else:
        text.append(NG._refractory)
    text.append('\\end{lstlisting}')

    text.append('\\item')
    text.append('\\textbf{Numerical Integration Method:}\\begin{lstlisting}')
    if isinstance(NG.method_choice, tuple):
        for x in NG.method_choice:
            text.append(x + ' ')
    else:
        text.append(NG.method_choice)
    text.append('\\end{lstlisting}')

    if isinstance(NG, SpatialNeuron):
        text.append(generate_SpatialNeuron_latex(NG))

    if log_dict is not None:
        for key in log_dict:
            if NG.name in key:  # if there is a subgroup of NG in keys of log_dict
                code = []
                for eq in log_dict[key]:
                    code.append(eq)

                text.append('\\item' + '\\textbf{' + replace_underscore(key) + ':}')
                text.append(convert_code_to_latex_listing('\n'.join(code)))

    text.append('\\end{itemize}')

    return '\n'.join(text)


def generate_network_graph(net, name):
    '''
    net: Network object in brian2

    generate a network graph
    '''
    def mark_NG(NG):
        '''
        Mark name and start stop of a NeuronGroup

        '''
        return NG.name + ' (' + str(NG.start) + ', ' + str(NG.stop) + ')'

    def link_Subgroup(SB):
        if isinstance(SB, Subgroup):
            g.edge(mark_NG(SB), mark_NG(SB.source))
            g.node(mark_NG(SB), shape='circle')
            g.node(mark_NG(SB.source), shape='doublecircle')

    g = Digraph('G', filename=name+'.gv')
    for obj in net.objects:
        if isinstance(obj, NeuronGroup):
            g.node(mark_NG(obj), shape='doublecircle')
        if isinstance(obj, Synapses):
            g.edge(mark_NG(obj.source), mark_NG(obj.target), label='<<b><i>' + obj.name + '</i></b>>', nodesep='1', minlen='4')
            g.node(mark_NG(obj.source), shape='doublecircle')
            g.node(mark_NG(obj.target), shape='doublecircle')
            link_Subgroup(obj.source)
            link_Subgroup(obj.target)
        if isinstance(obj, SpikeMonitor):
            g.edge(obj.name, mark_NG(obj.source))
            g.node(obj.name, shape='Msquare')
            g.node(mark_NG(obj.source), shape='doublecircle')
            link_Subgroup(obj.source)
        if isinstance(obj, StateMonitor):
            g.edge(obj.name, mark_NG(obj.source))
            g.node(obj.name, shape='box')
            g.node(mark_NG(obj.source), shape='doublecircle')
            link_Subgroup(obj.source)
        if isinstance(obj, PoissonInput):
            g.edge(obj.name, mark_NG(obj._group))
            g.node(obj.name, shape='rarrow')
            g.node(mark_NG(obj._group), shape='doublecircle')
            link_Subgroup(obj._group)
        if type(obj) is CodeRunner:
            g.edge(obj.name, mark_NG(obj.group))
            g.node(obj.name, shape='invtriangle')
            g.node(mark_NG(obj.group), shape='doublecircle')
    path = g.render(name, 'tmp', format='pdf')

    return '{' + path + '}'


def generate_syn_latex(syn):
    '''
    write the Synapses latex code into file.
    '''

    def generate_latex_synapse_on_pre(syn):
        str_pre_post = ''
        for x in syn._pathways:
            eqs = convert_code_to_latex_listing(x.code)
            if x.prepost == 'pre':
                str_pre_post += '\\item\n\\textbf{on pre:}\n' + replace_underscore(x.name) + eqs
            elif x.prepost == 'post':
                str_pre_post += '\\item\n\\textbf{on post:}\n' + replace_underscore(x.name) + eqs
            str_pre_post += '\\bigskip'

        return str_pre_post

    def generate_latex_synapse_on_event(syn):
        str_events = []
        if len(syn.events) > 0:
            str_events.append('\n\\item\\textbf{on events:}')
            str_events.append('\n\\begin{lstlisting}[language=Python,breaklines,showstringspaces=false]\n')
            for k, v in syn.events.items():
                str_events.append(k + ': ')
                str_events.append(v + '\n')
            str_events.append('\\end{lstlisting}')
        return ''.join(str_events)

    def plot_synapse(syn):
        pic_path = 'tmp/' + syn.name + '.pdf'
        plt.close()
        brian_plot(syn)
        pp.savefig(pic_path)
        NG_name = replace_underscore(syn.name)

        plt_string = []
        plt_string.append('\\item\n\\textbf{graph of ')
        plt_string.append(NG_name)
        plt_string.append(':}\\\\\n\\begin{center}\n\\includegraphics[width=\\textwidth]{')
        plt_string.append(pic_path)
        plt_string.append('}\n\\end{center}')

        return ''.join(plt_string)

    def generate_latex_synapse_summed_updateres(syn):
        syn_string = []
        if bool(syn.summed_updaters):
            syn_string.append('\\item\\textbf{Summedupdater:}')
            syn_string.append('\\begin{itemize}')
            for key, v in syn.summed_updaters.items():
                syn_string.append('\\item' + replace_underscore(key)+':')
                syn_string.append('\\begin{itemize}')
                syn_string.append('\\item clock dt: $' + v.clock.dt.in_best_unit() + '$' )
                syn_string.append('\\item when: ' + replace_underscore(str(v.when)))
                syn_string.append('\\item order: ' + replace_underscore(str(v.order)))
                syn_string.append('\\end{itemize}')
            syn_string.append('\\end{itemize}')

        return '\n'.join(syn_string)   

    syn_name = '\\section{Synapse ' + replace_underscore(syn.name) + '}'
    syn_string = []

    syn_string.append(syn_name)
    syn_string.append('\\begin{itemize}')
    #     syn_string.append('This is a Synapse group with following attributes:\\\\')
    if len(syn.equations) != 0:
        syn_string.append('\\item\\textbf{Model:}')
        syn_string.append(sympy.latex(syn.equations))
    syn_string.append(generate_latex_synapse_on_pre(syn))
    syn_string.append(generate_latex_synapse_on_event(syn))
    syn_string.append(plot_synapse(syn))
    syn_string.append(generate_latex_synapse_summed_updateres(syn))
    syn_string.append('\\end{itemize}')

    return '\n'.join(syn_string)


def generate_state_mon_latex(mon):
    '''
    write StateMonitor and SpikeMonitor group into file
    '''

    if len(mon.record_variables) != 1:
        warnings.warn('''brian_plot only works for a StateMonitor that records a single variable. 
                         So brian_docs will ignore StateMonitors which record more than one variables. 
                         For documentation of those StateMonitors, it is suggested to put those 
                         variables in different StateMonitors, and ensure that each StateMonitor
                         only has one variable''')
        return ''
    else:
        pic_path = 'tmp/' + mon.name + '.pdf'
        plt.close()
        brian_plot(mon)
        pp.savefig(pic_path)
        mon_name = replace_underscore(mon.name)

        text = []
        text. append('\\section{StateMonitor ' + mon_name + ':}')
        text.append('\\begin{center}')
        text.append('\\includegraphics[width=\\textwidth]{' + pic_path + '}')
        text.append('\\end{center}')
        if isinstance(mon.source, Subgroup):
            text.append('This graph records a subgroup start from ' + str(mon.source.start) + ', stop at ' + str(mon.source.stop) + '.')

        return '\n'.join(text)


def generate_spike_mon_latex(mon):
    '''
    write StateMonitor and SpikeMonitor group into file
    '''
    pic_path = 'tmp/' + mon.name + '.pdf'
    plt.close()
    brian_plot(mon)
    pp.savefig(pic_path)
    mon_name = replace_underscore(mon.name)

    text = []
    text.append('\\section{SpikeMonitor ' + mon_name + ':}')
    text.append('\\begin{center}')
    text.append('\\includegraphics[width=\\textwidth]{' + pic_path + '}')
    text.append('\\end{center}')
    if isinstance(mon.source, Subgroup):
        text.append('This graph records a subgroup start from ' + str(mon.source.start) + ', stop at ' + str(mon.source.stop) + '.')

    return '\n'.join(text)

def generate_constant_list(d):
    '''
    d: a dictionary of constant
    '''
    if not d:
        return ['No\\;Constant\\;Is\\;Documented']
    else:
        constant_list = []
        for key, value in d.items():
            if key.count('_') < 1:
                key_str = key
            elif key.count('_') == 1:
                l = key.split('_')
                key_str = l[0] + '_{' + l[1] + '}'
            else:
                key_str = '\\textit{' + replace_underscore(key) + '}'

            if isinstance(value, Quantity):
                constant_list.append(key_str + ': ' + sympy.latex(value.in_best_unit()))
                # constant_list.append(key_str + ': ' + value.in_best_unit(python_code=True))
            elif isinstance(value, str):
                constant_list.append(key_str + ': ' + sympy.latex(str_to_sympy(value)))
            else:
                constant_list.append(key_str + ': ' + str(value))

        return constant_list


def generate_tex_file(net, outputFile, constant_dict, log_dict, name):
    if not os.path.exists('tmp'):
        os.mkdir('tmp')

    file = open(outputFile, 'w')
    net_graph_path = generate_network_graph(net, name)
    net_graph_latex_path = net_graph_path.replace('\\', '/')

    net_list = []
    for obj in net.objects:
        if isinstance(obj, NeuronGroup):
            net_list.append(generate_ng_latex(obj, log_dict))
        if isinstance(obj, Synapses):
            net_list.append(generate_syn_latex(obj))
        if isinstance(obj, StateMonitor):
            net_list.append(generate_state_mon_latex(obj))
        if isinstance(obj, SpikeMonitor):
            net_list.append(generate_spike_mon_latex(obj))
        if isinstance(obj, PoissonInput):
            net_list.append(generate_PoissonInput_latex(obj))
        if type(obj) is CodeRunner:
            net_list.append(generate_CodeRunner_latex(obj))
    if constant_dict != None:
        constant_list = generate_constant_list(constant_dict)
    else:
        constant_list = ['No\\;Constant\\;Is\\;Documented']

    file_loader = FileSystemLoader(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
    env = Environment(loader=file_loader)
    template = env.get_template('template.txt')
    output = template.render(net_graph_latex_path=net_graph_latex_path, net_list=net_list, constant_list=constant_list)

    file.write(output)
    file.close()


def generate_log_dict(BrianLogger_tmp_log):
    '''
    explanations see create_NN_pdf
    '''
    if BrianLogger_tmp_log is not None:

        f = open(BrianLogger_tmp_log, "r")
        string = f.read()
        ll = re.findall('Creating code object \(group=.*\n[ ]*Key condition:\n[ ]*_cond = True\n[ ]*Key statement:\n[ ]*.*',
                        string)

        d = defaultdict(list)

        for x in ll:
            k = re.search('group=.*,', x).group(0).strip('group=').rstrip(',')
            v = re.search('Key statement:\n[ ]*.*', x).group(0).strip('Key statement:').strip()
            d[k].append(v)

        return d
    else:
        return None
def create_pdf(input_filename, output_filename):
    process = subprocess.Popen([
        'latex',  # Or maybe 'C:\\Program Files\\MikTex\\miktex\\bin\\latex.exe
        '-output-format=pdf',
        '-job-name=' + output_filename,
        input_filename])
    process.wait()

def  create_NN_pdf(net, name='net', constant_dict=None, BrianLogger_tmp_log=None):
    '''
    Top level function for generating a pdf document for a brian2 Network object.
    This function will generate a pdf document that has the specified name under the folder 'pdf'
    Other temporary file like the tex file and graphs used to generate the pdf will be under 'tmp' folder

    Parameters:
    -----------
    net: 'Network'
        a brian2 Network object that used to encapsulate all brian object created
    name: str, optional
        name of the document
    d: {str, 'Quantity'/str/int/float etc.}, optional
        a dictionary tant contains constants users want to document along with the Network
    BrianLogger_tmp_log: str
        the 'BrianLogger.tmp_log' parameter is a path for temporary log location to generate log_dict.

        log_dict is a defaultdict that contains mappings from name of an object(NeuronGroup and Synapse)to a list thant contains
        additional changes to that object.
        For example, in Kremer_et_al_2011_barrel_cortex example in Brian2 website, the statement
        >>> layer23exc.barrel_idx = 'floor(x) + floor(y)*barrelarraysize'
        won't be documented because this statement is not stored into the NeuronGroup object layer23.
        this information is extracted from BrianLogger.tmp_log.
        In oreder to use this feature, users need make sure the log is not deleted after a successful run.
        i.e. add this two lines of code after the import statement, andin front of your example:
        >>> BrianLogger.log_level_diagnostic()
        >>> prefs._set_preference('logging.delete_log_on_exit',False)

    '''
    tex_path = 'tmp/' + name + '.tex'
    pdf_path = 'pdf/' + name
    log_dict = generate_log_dict(BrianLogger_tmp_log)
    generate_tex_file(net, tex_path, constant_dict, log_dict, name)
    create_pdf(tex_path, pdf_path)
# Example usage:
# generate_tex_file(net, 'tmp/net.tex')
# create_pdf('tmp/net.tex', 'pdf/net')