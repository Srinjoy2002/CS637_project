#Comment if plotting normal or short 
all:
	#latexmk -lualatex -shell-escape plot
	latexmk -lualatex -shell-escape plot_short
	#latexmk -lualatex -shell-escape plot_fig2
	#latexmk -lualatex -shell-escape plot_fig3
	#latexmk -lualatex -shell-escape plot_fig4
	make -s clean

clean:
	rm -rf *.log *.fdb_latexmk *.fls *.aux */*.aux 