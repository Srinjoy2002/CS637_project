# Stealthy Computational Delay Attacks on control systems

This code is distributed for repeatability evaluation for the paper 'Stealthy computational delay attacks on control systems' 
by Talitha Nauta, Henrik Sandberg and Martina Maggio, accepted to ICCPS 2025. 

## Files
main.py defines the systems and global parameters, and it runs the other files using exec(optimise_{}.py).  
optimise_bin_chi2.py does the optimisation using both the binomial and the chi2 test.
optimise_bin.py does the optimisation using the binomial test.
optimise_chi2.py does the optimisation using the chi2 test.

The results are stored in the folders results_{bin/chi2/bin_chi2}/{system} and for each test configuration there are
two files named a{a_max}_p{p_miss}_alpha{significance_level}_w{window_length}. One csv file and one txt file. 
The csv file contains all information needed to make the plots, while the txt file contains extra information such as the sequences.

main_short.py does the same as main.py but only performs the test on system = furuta_zero, a_max = 3, p_miss = 0.25, window_length = 20, 
test=binomial and geometric
main_fig2.py does the same as main.py but only generates the data needed for Figure 2 in the paper
main_fig3.py does the same as main.py but only generates the data needed for Figure 3 in the paper
main_fig4.py does the same as main.py but only generates the data needed for Figure 4 in the paper

As the code adds new data sequences to the end of the csv and txt files you can't restart the code if the corresponding output folder already exists.
In the case where the figures contain the same data remove the already existing data folder before starting the new code, the code will not run otherwise. 

## Plot data
plot.tex creates a pdf with all the figures in the paper.
plot_short.tex creates a pdf with a figure for the short version.
plot_fig2.tex creates a pdf with Figure 2 in the paper.
plot_fig3.tex creates a pdf with Figure 3 in the paper.
plot_fig4.tex creates a pdf with Figure 4 in the paper.
The Makefile can be used to render the pdfs, comment the corresponding line for normal/short/fig{i}, or use the code below.
It is possible to create the plots even when the code is not finished with the longer sequences and visualise parts of the results.

To get the data for Table 1 check results_bin/furuta_hold/a4_p0.25_alpha0.01_w{10/12/14}.txt (!) length 27 (!) 
and remove the first and last zero from the attack_01 sequence. 

## Versions
python          3.12.2
gurobipy        11.0.1
numpy           1.26.4
scipy           1.12.0

## Install Gurobi and obtain a license
To install Gurobi and obtain a license follow the instructions on 
https://www.gurobi.com/features/academic-named-user-license/  

## Setting up a virtual environment
If your python installation supports venv to create virtual environments, the following commands would make it possible to create a virtual environment and run the code inside said virtual environment on a Linux. This requires that you have a Gurobi license, otherwise only parts of the execution will work.   

> cd REP

comment: navigate to the folder where you saved the reproducibility package REP

> python3 -m venv .

comment: this creates the folder bin and initializes the virtual environment

> source ./bin/activate

comment: this activates the virtual environment,
        your terminal shows (REP) at the beginning from now on
        
(REP) > python3 -m pip install gurobipy numpy scipy

comment: this installs the packages in the virtual environment

(REP) > python3 main_short.py

comment: expect this command to take approximately 2 hours

(REP) > latexmk -lualatex -shell-escape plot_short

comment: Render pdf with figure or use the Makefile instead

### Or on windows

> cd REP

comment: navigate to the folder where you saved the reproducibility package REP

> python -m venv .

comment: this creates the folder bin and initializes the virtual environment

> Scripts\activate

comment: this activates the virtual environment,
        your terminal shows (REP) at the beginning from now on
        
(REP) > python -m pip install gurobipy numpy scipy

comment: this installs the packages in the virtual environment

(REP) > python main_short.py

comment: expect this command to take 2 hours

(REP) > latexmk -lualatex -shell-escape plot_short

comment: Render pdf with figure



