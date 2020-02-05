import sys
import logging
import matplotlib.pyplot as plt
from cbsodata.utils import StatLineTable

logging.basicConfig(format='%(levelname)s : %(message)s', level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger()

# de tabel id kan je vinden door naar de data set te gaan op statline en in de url op te zoeken.
# in dit geval is de url: https://opendata.cbs.nl/#/CBS/nl/dataset/84410NED/table?ts=1568706226304
# dus we gaan een plaatje maken uit de tabel 84410NED
table_id = "84675NED"
question_id = 48
#table_id = "84410NED"
#question_id = 47

statline = StatLineTable(table_id=table_id)

statline.show_module_table(max_width=30)
statline.show_question_table(max_width=30)

df = statline.get_question_df(question_id=question_id)

logger.info(df.head())

#statline.modules_to_plot = 48

# statline.plot()
# statline.close_plots()

# toon de inhoud van de data nog een keer
statline.show_selection()
selection = [statline.selection_options[2],
             statline.selection_options[6],
             statline.selection_options[-1]]
statline.selection = selection
statline.apply_selection = True
logger.info(f"Select {selection}")

# verkrijg de vragen horen bij vraag 47
question_df = statline.get_question_df(question_id=question_id)

# haal de units op die horen bij vraag 47
units = question_df[statline.units_key].values[0]

# reorganiseer de data frame zodat we een bar plot van kunnen maken
question_df = statline.prepare_data_frame(question_df)

# open een nieuwe figur en maak de plot
fig, axis = plt.subplots()
fig.subplots_adjust(left=0.5, bottom=0.25, top=0.98)

question_df.plot(kind="barh", ax=axis)

# hier gaan we de boel tunen om er een CBS achtige plot van te maken
axis.set_ylabel("")
axis.set_xlabel(units)
axis.xaxis.set_label_coords(0.98, -0.1)
axis.legend(bbox_to_anchor=(0.01, 0.00), ncol=2, bbox_transform=fig.transFigure, loc="lower left",
            frameon=False)
for side in ["top", "bottom", "right"]:
    axis.spines[side].set_visible(False)
axis.spines['left'].set_position('zero')
axis.tick_params(which="both", bottom=False, left=False)
axis.xaxis.grid(True)
axis.yaxis.grid(False)
axis.invert_yaxis()

plt.show()
