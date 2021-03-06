import matplotlib.pyplot as plt
from cbsodata.utils import StatLineTable

# load the statline data
stat_line = StatLineTable(table_id="84410NED", apply_selection=True,
                          selection=['2 werkzame personen', '3 tot 5 werkzame personen'])

# select all the items beloning to question 47
df = stat_line.get_question_df(47)

# retrieve the module and questgion title and units from the data frame
units = df[stat_line.units_key].values[0]
section_title = df[stat_line.section_key].values[0]
module_title, question_title = section_title.split("\n")

# reorganise the data frame: the selections are put on the columns, the 
# question on the rows. 
df = stat_line.prepare_data_frame(df)

# initialise the plot
fig, ax = plt.subplots()
fig.subplots_adjust(left=0.5, bottom=0.15, top=0.85)

# make the plot
df.plot(kind='barh', ax=ax)

# all the bells and the wistle of the plot
ax.set_ylabel("")
ax.set_xlabel(units)

plt.figtext(0.05, 0.95, module_title, color="blue")
plt.figtext(0.05, 0.90, question_title, color="green")

ax.xaxis.set_label_coords(0.98, -0.1)
ax.legend(bbox_to_anchor=(0.01, 0.00), ncol=2,
          bbox_transform=fig.transFigure, loc="lower left", frameon=False)
for side in ["top", "bottom", "right"]:
    ax.spines[side].set_visible(False)
ax.spines['left'].set_position('zero')
ax.tick_params(which="both", bottom=False, left=False)
ax.xaxis.grid(True)
ax.yaxis.grid(False)
ax.invert_yaxis()
plt.show()
