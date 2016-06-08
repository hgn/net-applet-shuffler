
import os
import sys
import tools


# directory for data for NAME_1
DIRECTORY_WORK_1 = sys.argv[1]
# directory with data for NAME_2
DIRECTORY_WORK_2 = sys.argv[2]
# directory for output
DIRECTORY_OUTPUT = sys.argv[3]

NAME_1 = "Linux"
NAME_2 = "\"RFC 6298\""
PLOT_FILE_NAME = "dat.data"


def get_make_file_string():
    mk_file = str()
    mk_file += 'GNUPLOT_FILES = $(wildcard *.gpi)\n'
    mk_file += 'PNG_OBJ = $(patsubst %.gpi,%.png,  $(GNUPLOT_FILES))\n'
    mk_file += 'PDF_OBJ = $(patsubst %.gpi,%.pdf,  $(GNUPLOT_FILES))\n'
    mk_file += '\n'
    mk_file += 'all: $(PDF_OBJ)\n'
    mk_file += 'png: $(PNG_OBJ)\n'
    mk_file += '\n'
    mk_file += '%.eps: %.gpi *.data\n'
    mk_file += '\t@echo "compilation of "$<\n'
    mk_file += '\t@gnuplot $<\n'
    mk_file += '\n'
    mk_file += '%.pdf: %.eps\n'
    mk_file += '\t@echo "conversion in pdf format"\n'
    mk_file += '\t@epstopdf --outfile=$*.pdf $<\n'
    mk_file += '\t@echo "end"\n'
    mk_file += '\n'
    mk_file += '%.png: %.pdf\n'
    mk_file += '\t@echo "conversion in png format"\n'
    mk_file += '\t@convert -density 600 $< $*.png\n'
    mk_file += '\t@echo "end"\n'
    mk_file += '\n'
    mk_file += 'preview: all\n'
    mk_file += '\tfor i in $$(ls *.pdf); do xpdf -fullscreen $$i ; done\n'
    mk_file += '\n'
    mk_file += 'clean:\n'
    mk_file += '\t@echo "cleaning ..."\n'
    mk_file += '\t@rm -rf *.eps *.png *.pdf core\n'
    mk_file += '\n'
    mk_file += 'distclean: clean\n'
    mk_file += '\t@echo "distcleaning"\n'
    mk_file += '\t@rm -rf *.data\n'

    return mk_file


def get_plot_file_string():
    plot_file = str()
    plot_file += 'set terminal postscript eps enhanced color "Times" 25\n'
    plot_file += 'set output "ss-rtt.eps"\n'
    #plot_file += 'set title "Transmission Completion Time - Linux RTO vs. RFC 6298 RTO"\n'
    plot_file += '\n'
    plot_file += 'set style line 99 linetype 1 linecolor rgb "#999999" lw 2\n'
    plot_file += 'set key left top\n'
    plot_file += 'set key box linestyle 99\n'
    plot_file += 'set key spacing 1.2\n'
    plot_file += '\n'
    plot_file += 'set grid xtics ytics mytics\n'
    plot_file += '\n'
    plot_file += 'set size 1.3\n'
    plot_file += '\n'
    plot_file += 'set xlabel "Data Packets per Transmission"\n'
    plot_file += 'set ylabel "TCT [seconds]"\n'
    plot_file += 'set yrange [0:1.4]\n'
    plot_file += '\n'
    plot_file += 'A = "#228B22"; B = "#FF073D"\n'
    plot_file += 'set auto x\n'
    plot_file += 'set style data histogram\n'
    plot_file += 'set style histogram cluster gap 1\n'
    plot_file += 'set style fill solid border -1\n'
    plot_file += 'set boxwidth 0.9\n'
    plot_file += 'set xtic scale 0\n'
    plot_file += '\n'
    plot_file += 'plot "{}" using 2:xtic(1) ti col fc rgb A, \'\' u 3 ti col fc rgb B'.format(PLOT_FILE_NAME)
    plot_file += '\n'

    return plot_file


def make_directories_if_needed(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_file_list(directory):
    file_list = list()
    for file in os.listdir(directory):
        if "--" in file:
            if os.path.isfile(os.path.join(directory, file)):
                file_list.append(file)
    return sorted(file_list)


def get_data_string(list_of_triples):
    data_string = str()
    data_string += 'Title {} {}\n'.format(NAME_1, NAME_2)
    while list_of_triples:
        minimum = min(list_of_triples)
        list_of_triples.remove(minimum)
        data_string += '{} {} {}\n'.format(minimum[0], minimum[1], minimum[2])
    return data_string


def get_level_1_list():
    level_1_list = list()
    all_files_list = get_file_list(DIRECTORY_WORK_1)
    for file_name in all_files_list:
        level_1_name = file_name.split("--")[0]
        if level_1_name not in level_1_list:
            level_1_list.append(level_1_name)

    return level_1_list


def get_level_2_data_list(prefix):
    level_2_data_list = list()
    all_files_list = get_file_list(DIRECTORY_WORK_1)
    for file_name in all_files_list:
        if file_name.startswith(prefix):
            level_2_data_list.append(file_name.split("--")[1].split("_")[0])

    return level_2_data_list


def get_file_data_list(file_start_string, dir_1, dir_2):
    file_data_list = list()
    all_files_list = get_file_list(dir_1)
    for file_name in all_files_list:
        if file_name.startswith(file_start_string):
            first = file_name.split("--")[1].split("_")[0]
            file = open(os.path.join(dir_1, file_name), "r")
            second = file.read()
            file.close()
            file = open(os.path.join(dir_2, file_name), "r")
            third = file.read()
            file.close()
            file_data_list.append([int(first), second, third])
    return file_data_list


###############
###  START  ###
###############
lvl_1_list = get_level_1_list()
for lvl_1 in lvl_1_list:
    data_triple_list = get_file_data_list(lvl_1,
                                          DIRECTORY_WORK_1,
                                          DIRECTORY_WORK_2)
    data_str = get_data_string(data_triple_list)
    path_to_output = os.path.join(DIRECTORY_OUTPUT, lvl_1)
    make_directories_if_needed(path_to_output)

    # save files
    tools.save_string_to_file(os.path.join(path_to_output, PLOT_FILE_NAME),
                              data_str)
    tools.save_string_to_file(os.path.join(path_to_output, "Makefile"),
                              get_make_file_string())
    tools.save_string_to_file(os.path.join(path_to_output, "ss-rtt.gpi"),
                              get_plot_file_string())

    working_directory_backup = os.getcwd()
    os.chdir(path_to_output)
    tools.exec_locally("make")
    tools.exec_locally("make png")
    os.chdir(working_directory_backup)
    sys.stdout.write(".")
    sys.stdout.flush()

sys.stdout.write("\n")
sys.stdout.flush()

