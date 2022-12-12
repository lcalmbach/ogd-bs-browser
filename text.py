INFO = """Selecting a data provider fill the datasets grid with the available datasets for this provider. Select a record from the grid to display a summary of the dataset. When clicking on the link "open record at data provider" the dataset will be opened on the data providers ODS site. """

about = """
# About ODS Data Explorer 🚧
[Opendatasoft](https://www.opendatasoft.com/) is a French company that offers data-sharing software. Opendatasoft has developed a tool for sharing and reusing the data of companies and public administrations ([more](https://en.wikipedia.org/wiki/OpenDataSoft)). 

`ODS Data Explorer`, is a metadata-driven tool that has been independently developed to gain faster and more efficient access to ODS sites for specific tasks. The program is built on the ODS REST v2 API and uses ODSQL, which brings SQL-like database query features to the tool. This allows querying data and provides the use of filtering and aggregation of data. These features may prevent you from downloading large quantities of data in the case where you are interested in daily or monthly averages, minima, maxima etc. of high-frequency data.

### Menu:
#### 🔎Select Dataset
In the main window select one of the following data providers:
{}
Don't hestiate to contact the autor if you wish to include further sites to the tool.

In the box below the data provider, all available datasets for the data providers are displayed. You may filter the results by entering an expression in the title, by one or several themes, or by the datasets displayed in the last n days. The dataset list shows the id (unique dataset identifier), title, and issue date. You may sort the list according to any of these fields by clicking on the respective field in the header row.

Click on a record in the dataset list to load the respective metadata. The title of the dataset shows up below the dataset list and its main metadata is displayed on three tabs:
- Description: gives the introductory information shown on the information tab in the original ODS portal.
- Preview displays the first 1000 rows of the dataset and also shows the number of total records in the case where the number of records exceeds 1000.
- Fields: displays name, description, label and type for each field

#### Query
The original ODS portal software allows convenient filtering for predefined fields and downloading the full or filtered dataset. ODS Data Explorer allows, in addition, filtering for all fields and aggregating data. 

**Group by queries**
When selecting the group-by-query checkbox, you are required to enter the following information:
- Group by fields: the unique combination of fields for which you want to aggregate data, e.g.: for monthly average temperatures, the group fields should be: year, month
- Value fields: only a selection of numeric fields are shown. In the example above, you would select the temperature field.
- Aggregation function: How should the data be aggregated? In the sample above, you would select the `avg`-function, but you may also select min and max if you are as well interested in the extreme temperatures.

**Normal queries**
For standard queries without aggregation, the csv export has the advantage over the original ODS GUI in that you can use any field for filtering and that you may download or display only a selection of columns. The ODS-GUI is probably the better option in the case where you simply download the entire dataset. If you choose the ODS Data Explorer, proceed as follows:
- select the fields to be included in your query. If you leave the fields empty, all fields will automatically be included.
- click on add filter, then select fields a compare operator and a value. You may combine several filter criteria; they will be combined by a logical AND.
- Clicking on the show data button will load the data into a grid. Note that the record end-point of the ODS REST-API only allows 100 records to be fetched for each call and concatenates these results. Data loading is, therefore, slower than in the data preview. The latter, however, does not allow for aggregation and filtering. There is a limit of 9900 records to be loaded in the table; if you need to access more records, use either the Export button or the original ODS portal.
- Clicking on the `Export data` button will open a download window in a new tab. For this option, no data will show up in the GUI, the download will be stored on your local machine.


#### More Resources:
- [Opendatasoft data hub](https://data.opendatasoft.com/pages/home/)

"""