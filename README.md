TODO:
* create routine to upload generated .csv files to Google Firebase Cloud Storage for viewing through client code [option-chain-view](https://github.com/rolinmb/option-chain-view);

Do not use this program for financial advice, I am not responsible for any financial decisions you may make from the output of this program. I wrote this code purely as a learning experience and am uploading it here soley for others to learn about the design of a system like this.

To attest to my unwillingness to give financial advice, the program will not currently work for the provided CHAIN_BASE_URL in dummy_util.py. You'll have to edit getSoup() in dummy_util.py and probably the OptionChain and Option classes to parse the DataFrame and then .csv file in the same format as the current finoptions.py does

I have provided two potential other potential option chain data sources; but if they don't work, you'll have to actually pay for an option chain data API such as [Tradier](https://tradier.com/). I initially wrote this program to use the Tradier demo API but I guess I was making too many calls for a demo account... So if you don't pay for an API/data provider you'll have to keep jumping around sources like so.

Newer potential front-end to view the .csv and .png files with node.js/React.js in another repo called [option-chain-view](https://github.com/rolinmb/option-chain-view)

NOTE: This program expects the following folders & subfolders to exist in the same directory as main.py:
- /csv_outputs
    - chains
    - ohlc
- /png_outputs
    - chains

<- <b>finoptions.py</b> -> 

3 classes to define an OptionChain, the individual Option objects, as well as a ChainExpiration objects.

The OptionChain can be considered as a .csv file; a pandas DataFrame, a list of | ChainExpirations | , and/or two lists, | | Calls | , | Puts | |

You can build an OptionChain instance from a .csv file (will handle if the file you entered doesn't exist or isn't readable), or you can build an OptionChain w/o the .csv name parameter (will output to a default directory /csv_outputs/chains); which it will then fetch the HTML, parse and then create a .csv file alongside an object instance.

In the process of fetching the OptionChain HTML to scrape/parse, the program also fetches OHLC Time Series data from the AlphaVantage API in order to calculate Historical Volitility of the underlying asset. You may also pass in a .csv file of the OHLC Time Series; if not provided, then the AlphaVantage API is called and a .csv is saved to default in the directory /csv_outputs/ohlc.

If you are building an OptionChain from scratch; the program first checks if the ticker has Time Series data available to fetch, then will attempt to fetch the Option Chain HTML and parse to insure the ticker entered is optionable (has an option chain available).

<- <b>finmath.py</b> ->

Many functions to calculate relevant metrics of Option objects, as well as a fucntion for finding the underlying's standard deviation/historical volatilty and functions for simple/exponential/double exponential moving averages (moving averages only used in senti.py for now, but can be used on any pandas DataFrame column or pandas Series object).

Option objects are created on the fly when you define an OptionChain object.

If building an OptionChain from scratch (no .csv passed in), then the Option variables (such as Mid price, IV, MidIV, and all Option Greeks [Wikipedia](https://en.wikipedia.org/wiki/Greeks_(finance))) are calculated using all of the functions defined in this python file.

Otherwise, the .csv file output from a new OptionChain instance will already have these additional calculations and the Options are constructed with the values passed in as a parameter.

<- <b>av.py</b> ->

Short collection of functions to query the [AlphaVantage API](https://www.alphavantage.co/documentation/) to fetch OHLC Time Series data. Also performs price adjusting to accounti for stock splits, writes the DataFrame to a .csv, and returns the DataFrame to a new OptionChain instance.

Will first try to fetch a quote from AlphaVantage to verify the relevant ticker exists.

Needs your unique AlphaVantage API key saved in a file named av_config.py; the file dummy_av_config.py was provided as an example. It is free to sign up for the AlphaVantage API and start using many of their free endpoints.

<- <b>util.py</b> ->

Collection of helper functions and objects used in a variety of places throughout the program.

getSoup(): Used in finmath.py/OptionChain to fetch the Option Chain HTML, which requires Selenium to navigate and toggle elements on the page in order to make the Option Chain HTML fully visible. Beating the dead horse here; you'll have to refactor this method and parts of finoptions.py to use a different data source since CHAIN_BASE_URL as is will not be able to parse HTML as expected.

stripCommas() & parsePrice(): Used in getQuoteMW() to clean up parsed HTML for parsing into float()

getQuoteMW(): Fetches a quote from Market Watch for the specified ticker

validateTicker(): Uses getQuoteMW() to determine if the ticker exists before fetching Option Chain and/or Time Series data

<- <b>surface.py</b> ->

Uses matplotlib.pyplot to create surface visualizations of the OptionChain objects. Also contains functions for getting the lists of data used to represent the surfaces for further calculations (like finding surface gradients/gradient fields)

buildChainSurfaceLists(): returns two lists (Call and Put surfaces), where each list contains the same number of sublists (length = number of expration dates on the Option Chain) representing data for each expiration date for the individual Call or Put surface. Each surface sublist (representing a unique time to expiration) contains 3 sub-sublists;

- Call or Put list [ [[X list], [Y list], [Z list]], [[X list], [Y list], [Z list]], ...]
    - List of unique Times to Expiration (equivalently the unique Expriation Dates) for that OptionChain
        - X list = Time to Expiration date (the unique time to expiration, constant values)
        - Y list = Strike Price of unique Expiration date (all strike prices of the specific time to expiration)
        - Z list = Caluclation for Call or Put Option at X,Y (calculated values for all strikes specific to that unique time to expiration)

buildChainSurfacePlots(): Calls buildChainSurfacesLists() and dual_mesh_plot_3d() to construct a 2-plot 3d visualizaion of the calculated OptionChain Call & Put surfaces.

buildChainSurfacePoints(): returns two lists (Call and Put surfaces), where each list contains sublists of individual surface point time to X (expiration), Y(strike price), Z data for the respective Call or Put surface;

- Call or Put list [ [X, Y, Z], [X, Y, Z], [X, Y, Z],  ...]
    - Points list
        - X = Time to Expiration of specific Option
        - Y = Strike Price of specific Option
        - Z = Calculation for specific Option

buildChainGradientFields(): View 3d plot of calculated OptionChain Call & Put surface gradient vectors. WARNING: this tends to slow down your computer a lot, use with care or just save to an image output to view if you have a slow computer.

buildChainGradientPlots(): View 3d plot of calculated OptionChain Call & Put surface gradients.

buildChainSurfacePlots2(): Calls quad_mesh_plot_3d(), buildChainSurfaceLists() and buildChainSurfacePoints() to construct a 4-plot 3d visualization of the calculatied OptionChain Call & Put surfaces alongside those surfaces' respective gradient surfaces.

<- <b>test.py</b> ->

Tests for all combinations of constructor parameters of OptionChain objects. Also tests av.py fetch methods and simple 2-plot OptionChain surface visualization for default IV calculated surface.

<- <b>main.py</b> ->

Routine to create .png files for various calculated surfaces for a specific ticker/set of tickers. Can comment/uncomment code to pass a single ticker via command line argument. Mainly just used as a script to collect OptionChain data, Time Series data and .png files for all calculated surfaces for any optionable ticker.

<- <b>/proto_view:</b> ->

HTML and JavaScript code to view the Time Series .csv data using Plotly.js (via CDN link); and also displays the OptionChain .csv as a table, and displays the relevant .png surface images for the ticker found in the OptionChain .csv file

=> /proto_view is essentially my testing ground for the view/React app code located at my other repo [option-chain-view](https://github.com/rolinmb/option-chain-view), try and make your own visuals yourself!

<- <b>rk4.py</b> ->

TODO: Implmement Runge-Kutta 4 method to simulate the soltion of the Black-Scholes P.D.E specifically using theta's derivation from original formula;
You end up with the I.V.P; theta = dV/dt = f(t,v) where V(t0) = V0 (eta, current contract value); take step-size h and n iterations to advance;