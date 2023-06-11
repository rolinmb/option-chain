NOTE: This program expects the following folders to exist in the same directory as main.py:
- /csv_outputs
    - chains
    - ohlc
    - senti
- /png_outputs
    - chains


<- finoptions.py -> 

3 classes to define an OptionChain, the individual Option objects, as well as a ChainExpiration objects.

The OptionChain can be considered as a .csv file; a pandas DataFrame, a list of | ChainExpirations | , and/or two lists, | | Calls | , | Puts | |

You can build an OptionChain instance from a .csv file (will handle if the file you entered doesn't exist or isn't readable), or you can build an OptionChain w/o the .csv name parameter (will output to a default directory /csv_outputs/chains); which it will then fetch the HTML, parse and then create a .csv file alongside an object instance.

In the process of fetching the OptionChain HTML to scrape/parse, the program also fetches OHLC Time Series data from the AlphaVantage API in order to calculate Historical Volitility of the underlying asset. You may also pass in a .csv file of the OHLC Time Series; if not provided, then the AlphaVantage API is called and a .csv is saved to default in the directory /csv_outputs/ohlc.

If you are building an OptionChain from scratch; the program first checks if the ticker has Time Series data available to fetch, then will attempt to fetch the Option Chain HTML and parse to insure the ticker entered is optionable (has an option chain available).

<- finmath.py ->

Many functions to calculate relevant metrics of Option objects, as well as a fucntion for finding the underlying's standard deviation/historical volatilty and functions for simple/exponential/double exponential moving averages (moving averages only used in senti.py for now, but can be used on any pandas DataFrame column or pandas Series object).

Option objects are created on the fly when you define an OptionChain object.

If building an OptionChain from scratch (no .csv passed in), then the Option variables (such as Mid price, IV, MidIV, and all Option Greeks [Wikipedia](https://en.wikipedia.org/wiki/Greeks_(finance))) are calculated using all of the functions defined in this python file.

Otherwise, the .csv file output from a new OptionChain instance will already have these additional calculations and the Options are constructed with the values passed in as a parameter.

<- av.py ->

Short collection of functions to query the [AlphaVantage API](https://www.alphavantage.co/documentation/) to fetch OHLC Time Series data. Also performs price adjusting to accounti for stock splits, writes the DataFrame to a .csv, and returns the DataFrame to a new OptionChain instance.

Will first try to fetch a quote from AlphaVantage to verify the relevant ticker exists.

Needs your unique AlphaVantage API key saved in a file named av_config.py; the file dummy_av_config.py was provided as an example. It is free to sign up for the AlphaVantage API and start using many of their free endpoints.

<- util.py ->

Collection of helper functions and objects used in a variety of places throughout the program.

getSoup(): Used in finmath.py/OptionChain to fetch the Option Chain HTML, which requires Selenium to navigate and toggle elements on the page in order to make the Option Chain HTML fully visible.

stripCommas() & parsePrice(): Used in getQuoteMW() to clean up parsed HTML for parsing into float()

getQuoteMW(): Fetches a quote from Market Watch for the specified ticker

validateTicker(): Uses getQuoteMW() to determine if the ticker exists before fetching Option Chain and/or Time Series data

<- surface.py ->

Uses matplotlib.pyplot to create surface visualizations of the OptionChain objects. Also contains functions for getting the lists of data used to represent the surfaces for further calculations (like finding surface gradients/gradient fields)

buildChainSurfaceLists(): returns two lists (Call and Put surfaces), where each list contains the same number of sublists (length = number of expration dates on the Option Chain) representing data for each expiration date for the individual Call or Put surface. Each surface sublist (representing a unique time to expiration) contains 3 sub-sublists;

- Call or Put list
    - List of unique Times to Expiration (equivalently the unique Expriation Dates) for that OptionChain
        - X list = Time to Expiration date (the unique time to expiration, constant values)
        - Y list = Strike Price of unique Expiration date (all strike prices of the specific time to expiration)
        - Z list = Caluclation for Call or Put Option at X,Y (calculated values for all strikes specific to that unique time to expiration)

buildChainSurfacePlots(): Calls buildChainSurfacesLists() and dual_mesh_plot_3d() to construct a 2-plot 3d visualizaion of the calculated OptionChain Call & Put surfaces.

buildChainSurfacePoints(): returns two lists (Call and Put surfaces), where each list contains sublists of individual surface point time to X (expiration), Y(strike price), Z data for the respective Call or Put surface;

- Call or Put list
    - Points list
        - X = Time to Expiration of specific Option
        - Y = Strike Price of specific Option
        - Z = Calculation for specific Option

buildChainGradientFields(): View 3d plot of calculated OptionChain Call & Put surface gradient vectors. WARNING: this tends to slow down your computer a lot, use with care or just save to an image output to view if you have a slow computer.

buildChainGradientPlots(): View 3d plot of calculated OptionChain Call & Put surface gradients.

buildChainSurfacePlots2(): Calls quad_mesh_plot_3d(), buildChainSurfaceLists() and buildChainSurfacePoints() to construct a 4-plot 3d visualization of the calculatied OptionChain Call & Put surfaces alongside those surfaces' respective gradient surfaces.

<- test.py ->

Tests for all combinations of constructor parameters of OptionChain objects. Also tests av.py fetch methods and simple 2-plot OptionChain surface visualization for default IV calculated surface.

<- senti.py ->

Scrapes headlines from a set of tickers and applies sentiment scores (via ntlk) to each headline in order to come up with a daily average sentiment score. Creates a plot of historical average daily sentiment scores w/ moving averages (finmath.py) using matplotlib.

<- senti_config.py ->

List of tickers to scrape headlines off of [FinViz](https://finviz.com/) and a list of ntlk vader sentiment scores for analyzing the tone of headlines.

<- main.py ->

Routine to create .png files for various calculated surfaces for a specific ticker/set of tickers. Can comment/uncomment code to pass a single ticker via command line argument. Mainly just used as a script to collect OptionChain data, Time Series data and .png files for all calculated surfaces for any optionable ticker.