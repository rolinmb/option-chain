from finoptions import *
import numpy as np
from scipy.interpolate import griddata
'''<-------->
if you want to show matplotlib plots in main.py or test.py
uncomment these two lines
   <-------->'''
import matplotlib
matplotlib.use('agg')
'''<-------->'''
from matplotlib import cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def getMeshGrid(X, Y, Z):
    XX, YY = np.meshgrid(np.linspace(min(X), max(X), 230), np.linspace(min(Y), max(Y), 230))
    ZZ = griddata(np.array([X, Y]).T, np.array(Z), (XX,YY), method='linear')
    return XX, YY, ZZ

def combineData(xyz_data):
    all_X = []
    all_Y = []
    all_Z = []
    for d in xyz_data: # every d in data is a list with 3 list
        [all_X.append(x) for x in d[0]]
        [all_Y.append(y) for y in d[1]]
        [all_Z.append(z) for z in d[2]]
    return all_X, all_Y, all_Z

def single_mesh_plot3D(xyz_data, title):
    fig = plt.figure()
    fig.suptitle(title)
    ax = Axes3D(fig, azim=-29, elev=40, auto_add_to_figure=False)
    ax.set_xlabel('TTE')
    ax.set_ylabel('Strike Price ($)')
    all_X , all_Y, all_Z = combineData(xyz_data)
    XX, YY, ZZ = getMeshGrid(all_X, all_Y, all_Z)
    ax.plot_surface(XX, YY, ZZ,
        rstride=3, cstride=3, cmap=cm.gnuplot2,
        linewidth=0, antialiased=False)
    ax.contour(XX, YY, ZZ)
    fig.add_axes(ax)
    plt.show()
    plt.close()

def dual_mesh_plot3D(ticker, method_name, call_data, put_data):
    fig = plt.figure()
    fig.set_size_inches(10,10)
    fig.suptitle('%s Option Chain %s Surfaces'%(ticker, method_name), fontsize=16)
    # Call surface plot
    c_ax = fig.add_subplot(1, 2, 1, projection='3d')
    c_ax.set_xlabel('Call TTE (Yrs)')
    c_ax.set_ylabel('Call Strike Price ($)')
    c_ax.title.set_text('%s Calls %s'%(ticker, method_name))
    c_all_X, c_all_Y, c_all_Z = combineData(call_data)
    cXX, cYY, cZZ = getMeshGrid(c_all_X, c_all_Y, c_all_Z)
    c_ax.plot_surface(cXX, cYY, cZZ,
        rstride=3, cstride=3, cmap=cm.gnuplot2,
        linewidth=0, antialiased=False)
    c_ax.contour(cXX, cYY, cZZ)
    # Put surface plot
    p_ax = fig.add_subplot(1, 2, 2, projection='3d')
    p_ax.set_xlabel('Put TTE (Yrs)')
    p_ax.set_ylabel('Put Strike Price ($)')
    p_ax.title.set_text('%s Puts %s'%(ticker, method_name))
    p_all_X, p_all_Y, p_all_Z = combineData(put_data)
    pXX, pYY, pZZ = getMeshGrid(p_all_X, p_all_Y, p_all_Z)
    p_ax.plot_surface(pXX, pYY, pZZ,
        rstride=3, cstride=3, cmap=cm.gnuplot2,
        linewidth=0, antialiased=False)
    p_ax.contour(pXX, pYY, pZZ)
    fig.savefig('png_outputs/%s_%s_dualsurface.png'%(ticker, method_name), dpi=100)
    plt.show()
    plt.close()

def buildDateXYZData(options, exp_strikes, exp_tte, ticker, method_name, calc_method=getOptionIV, logging=True):
    dateX = []
    dateY = []
    dateZ = []
    for i in range(0, len(exp_strikes)):
        strike = exp_strikes[i]
        new_data = calc_method(options[i])
        dateX.append(exp_tte)                 # X = Time To Expiration
        dateY.append(strike)                  # Y = strike price
        dateZ.append(calc_method(options[i])) # Z = calculation
        if logging:
                print('buildDateXYZData():\t\t^ %s $%s %s %s: %s'%(ticker, strike, options[i].callOrPut(), method_name, round(new_data, 5)))
    return dateX, dateY, dateZ

def buildChainSurfaceLists(chain, calc_method=getOptionIV, logging=True):
    method_name = calc_method.__name__.split('getOption', 1)[1]
    call_data = []
    put_data = []
    expirations = chain.getExpirationsList()
    ticker = chain.getTicker()
    for expiry in expirations:
        exp_options = expiry.getOptions()
        exp_strikes = expiry.getExpirationStrikes()
        exp_tte = expiry.getTTE()
        if logging:
            print('buildChainSurfaceLists():\t* Processing grid data %s %s Expiry (TTE: %s years)'%(ticker, expiry.getDateStr(), abs(exp_tte)))
        d_cx, d_cy, d_cz = buildDateXYZData(
            exp_options[0], exp_strikes, exp_tte, ticker,
            method_name, calc_method, logging=logging
        ) # Calls
        d_px, d_py, d_pz = buildDateXYZData(
            exp_options[1], exp_strikes, exp_tte, ticker, 
            method_name, calc_method, logging=logging
        ) # Puts
        call_data.append([d_cx, d_cy, d_cz])
        put_data.append([d_px, d_py, d_pz])
        if logging:
            print('buildChainSurfaceLists():\t-> Finished %s %s Expiry (TTE: %s years)'%(ticker, expiry.getDateStr(), abs(exp_tte)))
    if logging:
        print('buildChainSurfaceLists():\t* All %s ChainExpirations processed, OptionChain successfully read; now generating plots...'%ticker)
    # Data format = [ [[X=day_tte (same for given day)], [Y=day_strikes], [Z=day_vals]], [[], [], []], ... ]; 
    # Each element of call_data & put_data is a list containing 3 lists: [[X=day_tte (same for given day)], [Y=day_strikes], [Z=day_vals]]
    return call_data, put_data

def buildChainSurfacePlots(chain, calc_method=getOptionIV, logging=True):
    method_name = calc_method.__name__.split('getOption', 1)[1]
    call_data, put_data = buildChainSurfaceLists(chain, calc_method=calc_method, logging=logging)
    # Build 3D Mesh Plots after populating call and put data
    dual_mesh_plot3D(
        chain.getTicker(), method_name,
        call_data, put_data,
    )

def buildChainSurfacePoints(chain, calc_method=getOptionIV, logging=True):
    method_name = calc_method.__name__.split('getOption', 1)[1]
    call_data, put_data = buildChainSurfaceLists(chain, calc_method=calc_method, logging=False)
    call_point_data = []
    put_point_data = []
    for c_day_data in call_data:
        c_exp = c_day_data[0][0]
        for i in range(0, len(c_day_data[0])):
            call_point_data.append([c_exp, c_day_data[1][i], c_day_data[2][i]])
        if logging:
            c_msg = '''buildChainSurfacePoints(): %s Call %s Surface Expiry/TTE = %s (Yrs) Data;
            \n\t-> Expiry Call Strikes: %s
            \t-> Expiry Call %s Calculations: %s
            '''%(chain.getTicker(), method_name, c_exp, c_day_data[1], method_name, c_day_data[2])
            print(c_msg)
    for p_day_data in put_data:
        p_exp = p_day_data[0][0]
        for i in range(0, len(p_day_data[0])):
            put_point_data.append([p_exp, p_day_data[1][i], p_day_data[2][i]])
        if logging:
            p_msg = '''buildChainSurfacePoints(): %s Put %s Surface Expiry/TTE = %s (Yrs) Data;
            \n\t-> Expiry Put Strikes: %s
            \t-> Expiry Put %s Calculations: %s
            '''%(chain.getTicker(), method_name, p_exp, p_day_data[1], method_name, p_day_data[2])
            print(p_msg)
    if logging:
        print('buildChainSurfacePoints():\n%s Call %s Surface XYZ Point Data;'%(chain.getTicker(), method_name))        
        for c_point in call_point_data:
                print('\t-> %s Call Point:  %s'%(chain.getTicker(), c_point))
        print('buildChainSurfacePoints():\n%s Put %s Surface XYZ Point Data;'%(chain.getTicker(), method_name))
        for p_point in put_point_data:
                print('\t-> %s Put Point: %s'%(chain.getTicker(), p_point))
    # Data format = [[x0,y0,z0], [x1,y1,z1], [x2,y2,z2], [x3,y3,z3], ...]
    # Each element of call_point_data & put_point_data is a list containing 3 values: [X,Y,Z] for the corresoponding Call/Put calc_method surface
    return call_point_data, put_point_data

def buildChainGradientFields(chain, calc_method=getOptionIV, logging=True):
    funct_name = calc_method.__name__.split('getOption', 1)[1]
    # Get point lists to calculate gradients from
    call_point_data, put_point_data = buildChainSurfacePoints(chain, calc_method=calc_method, logging=False)
    # Get call and put arrays/lists to build vector field meshplot for 3D vector points
    call_data, put_data = buildChainSurfaceLists(chain, calc_method=calc_method, logging=False)
    callsX, callsY, callsZ = combineData(call_data)
    cX_grid, cY_grid, cZ_grid = getMeshGrid(callsX, callsY, callsZ)
    putsX, putsY, putsZ = combineData(put_data)
    pX_grid, pY_grid, pZ_grid = getMeshGrid(putsX, putsY, putsZ)
    # Gradients taken from point data lists; returns 2 arrays, gradient w.r.t. TTE & gradient w.r.t Strike
    call_grad = np.gradient(call_point_data)
    put_grad = np.gradient(put_point_data)
    if logging:
        print('* %s Call %s Gradient;\n%s'%(chain.getTicker(), funct_name, call_grad))
        print('* %s Put %s Gradient;\n%s'%(chain.getTicker(), funct_name, put_grad))
    # Building grid data for Call gradient vector field
    grad_cX = []
    grad_cY = []
    grad_cZ = []
    grad_pX = []
    grad_pY = []
    grad_pZ = []
    # Iterate over all options in the chain to find Call and Put gradient resultant vectors
    for i in range(0, chain.getUniqueStrikesCount()):
        grad_cX.append(call_grad[1][i][0] - call_grad[0][i][0]) # Call gradient resulting vector w.r.t. TTE
        grad_cY.append(call_grad[1][i][1] - call_grad[0][i][1]) # Call gradient resulting vector w.r.t strike price
        grad_cZ.append(call_grad[1][i][2] - call_grad[0][i][2]) # Call gradient resulting vector w.r.t. calc_method surface value
        if logging:
            print('\t~ %s Call %s Gradient Points:\n\t\t* w.r.t TTE: %s\n\t\t* w.r.t. strike price: %s'%(chain.getTicker(), funct_name, call_grad[0][i], call_grad[1][i]))
            print('\t\t=> %s Call %s Gradient Resultant Vector:\n\t\t\t=> %s'%(chain.getTicker(), funct_name, (call_grad[0][i] + call_grad[1][i])))
        grad_pX.append(put_grad[1][i][0] - put_grad[0][i][0])   # Put gradient resulting vector w.r.t. TTE
        grad_pY.append(put_grad[1][i][1] - put_grad[0][i][1])   # Put gradient resulting vector w.r.t strike price
        grad_pZ.append(put_grad[1][i][2] - put_grad[0][i][2])   # Put gradient resulting vector w.r.t. calc_method surface value
        if logging:
            print('\t~ %s Put %s Gradient Points:\n\t\t* w.r.t TTE: %s\n\t\t* w.r.t. strike price: %s'%(chain.getTicker(), funct_name, put_grad[0][i], put_grad[1][i]))
            print('\t\t=> %s Put %s Gradient Resultant Vector:\n\t\t\t=> %s'%(chain.getTicker(), funct_name, (put_grad[0][i] + put_grad[1][i])))
    if logging:
        print('Number of unique strikes on %s OptionChain (i.e. length of OptionChain.df.index): %s'%(chain.getTicker(), chain.getUniqueStrikesCount()))
        print('Shape of %s call_data: %s by %s'%(chain.getTicker(), len(call_data[0]), len(call_data[0][0])))
        print('Shape of %s put_data: %s by %s'%(chain.getTicker(), len(put_data[0]), len(put_data[0][0])))
        print('Shape of %s Call Gradient 1: %s'%(chain.getTicker(), call_grad[0].shape))
        print('Shape of %s Call Gradient 2: %s'%(chain.getTicker(), call_grad[1].shape))
        print('\t-> Length of grad_cX: %s'%len(grad_cX))
        print('\t-> Length of grad_cY: %s'%len(grad_cY))
        print('\t-> Length of grad_cZ: %s'%len(grad_cZ))
        print('Shape of %s Put Gradient 1: %s'%(chain.getTicker(), put_grad[0].shape))
        print('Shape of %s Put Gradient 2: %s'%(chain.getTicker(), put_grad[1].shape))
        print('\t-> Length of grad_pX: %s'%len(grad_pX))
        print('\t-> Length of grad_pY: %s'%len(grad_pY))
        print('\t-> Length of grad_pZ: %s'%len(grad_pZ))
    # Get mesh grid of Call and Put resulting gradient vectors
    grad_cXX, grad_cYY, grad_cZZ  = getMeshGrid(grad_cX, grad_cY, grad_cZ)
    grad_pXX, grad_pYY, grad_pZZ = getMeshGrid(grad_pX, grad_pY, grad_pZ)
    # Generate color map for Call vector field by azimuth angle
    call_color = np.arctan2(grad_cYY, grad_cXX)
    call_color = (call_color.ravel() - call_color.min()) / call_color.ptp()
    call_color = np.concatenate((call_color, np.repeat(call_color, 3)))
    call_color = plt.cm.hsv(call_color)
    # Generate color map for Put vector field by azimuth angle
    put_color = np.arctan2(grad_pYY, grad_pXX)
    put_color = (put_color.ravel() - put_color.min()) / put_color.ptp()
    put_color = np.concatenate((put_color, np.repeat(put_color, 3)))
    put_color = plt.cm.hsv(put_color)
    # Plotting both Call & Put gradient vector fields
    fig = plt.figure()
    fig.set_size_inches(10,10)
    fig.suptitle('%s Option Chain %s Gradient Vector Fields'%(chain.getTicker(), funct_name), fontsize=16)
    c_ax = fig.add_subplot(1, 2, 1, projection='3d') # Call gradient vector field
    c_ax.set_xlabel('Call TTE (Yrs)')
    c_ax.set_ylabel('Call Strike Price ($)')
    c_ax.title.set_text('%s Call %s grad Vector Field'%(chain.getTicker(), funct_name))
    c_ax.quiver(cX_grid, cY_grid, cZ_grid, grad_cXX, grad_cYY, grad_cZZ,
        colors=call_color, length=0.00025)
    p_ax = fig.add_subplot(1, 2, 2, projection='3d') # Put gradient vector field
    p_ax.set_xlabel('Put TTE (Yrs)')
    p_ax.set_ylabel('Put Strike Price ($)')
    p_ax.title.set_text('%s Put %s grad Vector Field'%(chain.getTicker(), funct_name))
    p_ax.quiver(pX_grid, pY_grid, pZ_grid, grad_pXX, grad_pYY, grad_pZZ, 
        colors=put_color, length=0.00025)
    fig.savefig('png_outputs/%s_%s_gradfield.png'%(chain.getTicker(), funct_name), dpi=100)
    plt.show()
    plt.close()


def buildChainGradientPlots(chain, calc_method=getOptionUltima, logging=True):
    funct_name = calc_method.__name__.split('getOption', 1)[1]
    # Get point lists to calculate gradients from
    call_point_data, put_point_data = buildChainSurfacePoints(chain, calc_method=calc_method, logging=False)
    # Get call and put arrays/lists to build vector field meshplot for 3D vector points
    call_data, put_data = buildChainSurfaceLists(chain, calc_method=calc_method, logging=False)
    callsX, callsY, callsZ = combineData(call_data)
    putsX, putsY, putsZ = combineData(put_data)
    # Gradients taken from point data lists; returns 2 arrays, gradient w.r.t. TTE & gradient w.r.t Strike
    call_grad = np.gradient(call_point_data)
    put_grad = np.gradient(put_point_data)
    if logging:
        print('* %s Call %s Gradient;\n%s'%(chain.getTicker(), funct_name, call_grad))
        print('* %s Put %s Gradient;\n%s'%(chain.getTicker(), funct_name, put_grad))
    # Building the magnitudes for plotting by calculating Gradient resultant vectors for each unique option
    grad_c_mags = []
    grad_p_mags = []
    # Iterate over all options in the chain to find Call and Put gradient resultant vectors
    for i in range(0, chain.getUniqueStrikesCount()):
        new_c_mag = np.sqrt(((call_grad[1][i][0] - call_grad[0][i][0])**2) + ((call_grad[1][i][1] - call_grad[0][i][1])**2) + ((call_grad[1][i][2] - call_grad[0][i][2])**2))
        grad_c_mags.append(new_c_mag) # Call gradient resultant vector magnitude
        if logging:
            print('\t~ %s Call %s Gradient Points:\n\t\t* w.r.t TTE: %s\n\t\t* w.r.t. strike price: %s'%(chain.getTicker(), funct_name, call_grad[0][i], call_grad[1][i]))
        new_p_mag = np.sqrt(((put_grad[1][i][0] - put_grad[0][i][0])**2) + ((put_grad[1][i][1] - put_grad[0][i][1])**2) + ((put_grad[1][i][2] - put_grad[0][i][2])**2))
        grad_p_mags.append(new_p_mag) # Put gradient resultant vector magnitude
        if logging:
            print('\t~ %s Put %s Gradient Points:\n\t\t* w.r.t TTE: %s\n\t\t* w.r.t. strike price: %s'%(chain.getTicker(), funct_name, put_grad[0][i], put_grad[1][i]))
    # Get meshgrids to plotting using Gradient vector magnitudes for Z
    cX_grid, cY_grid, cZ_grid = getMeshGrid(callsX, callsY, grad_c_mags) 
    pX_grid, pY_grid, pZ_grid = getMeshGrid(putsX, putsY, grad_p_mags)
    # Plotting both Call & Put gradient magniutde surfaces
    fig = plt.figure()
    fig.set_size_inches(10,10)
    fig.suptitle('%s Option Chain %s Gradient Magnitudes'%(chain.getTicker(), funct_name), fontsize=16)
    c_ax = fig.add_subplot(1, 2, 1, projection='3d')
    c_ax.set_xlabel('Call TTE (Yrs)')
    c_ax.set_ylabel('Call Strike Price ($)')
    c_ax.title.set_text('%s Call %s ||grad||'%(chain.getTicker(), funct_name))
    c_ax.plot_surface(cX_grid, cY_grid, cZ_grid,
        rstride=3, cstride=3, cmap=cm.gnuplot2,
        linewidth=0, antialiased=False)
    p_ax = fig.add_subplot(1, 2, 2, projection='3d')
    p_ax.set_xlabel('Put TTE (Yrs)')
    p_ax.set_ylabel('Put Strike Price ($)')
    p_ax.title.set_text('%s Put %s ||grad||'%(chain.getTicker(), funct_name))
    p_ax.plot_surface(pX_grid, pY_grid, pZ_grid,
        rstride=3, cstride=3, cmap=cm.gnuplot2,
        linewidth=0, antialiased=False)
    fig.savefig('png_outputs/%s_%s_gradsurface.png'%(chain.getTicker(), funct_name), dpi=100)
    plt.show()
    plt.close()

def quad_mesh_plot_3d(ticker, method_name, c_data, p_data, cgrad_mdata, pgrad_mdata, showing=False):
    # Plotting 2x2 Grid of 3D Plots
    fig = plt.figure()
    fig.set_size_inches(11,11)
    # fig.suptitle('%s Option Chain %s Surfaces & Surface Gradient Magnitudes'%(ticker, method_name), fontsize=12)
    # Calls method_name surface
    ax_c = fig.add_subplot(2, 2, 1, projection='3d')
    ax_c.view_init(70, 170)
    ax_c.set_title('Call %s'%method_name, fontsize=10)
    ax_c.set_xlabel('YTE', fontsize=8)
    ax_c.set_ylabel('Strike', fontsize=8)
    cX, cY, cZ = combineData(c_data)
    cXX, cYY, cZZ = getMeshGrid(cX, cY, cZ)
    ax_c.plot_surface(cXX, cYY, cZZ,
        rstride=3, cstride=3, cmap=cm.gnuplot2,
        linewidth=0, antialiased=False)
    # Puts method_name surface
    ax_p = fig.add_subplot(2, 2, 2, projection='3d')
    ax_p.view_init(70, 170)
    ax_p.set_title('Put %s'%method_name, fontsize=10)
    ax_p.set_xlabel('YTE', fontsize=8)
    ax_p.set_ylabel('Strike', fontsize=8)
    pX, pY, pZ = combineData(p_data)
    pXX, pYY, pZZ = getMeshGrid(pX, pY, pZ)
    ax_p.plot_surface(pXX, pYY, pZZ,
        rstride=3, cstride=3, cmap=cm.gnuplot2,
        linewidth=0, antialiased=False)
    # Calls Gradient magnitude surface
    ax_gc = fig.add_subplot(2, 2, 3, projection='3d')
    ax_gc.view_init(70, 170)
    ax_gc.set_title('Call %s ||grad||'%method_name, fontsize=10)
    ax_gc.set_xlabel('YTE', fontsize=8)
    ax_gc.set_ylabel('Strike', fontsize=8)
    cgXX, cgYY, cgZZ = getMeshGrid(cX, cY, cgrad_mdata)
    ax_gc.plot_surface(cgXX, cgYY, cgZZ,
        rstride=3, cstride=3, cmap=cm.gist_gray,
        linewidth=0, antialiased=False)
    # Puts Gradient magnitude surface
    ax_gp = fig.add_subplot(2, 2, 4, projection='3d')
    ax_gp.view_init(70, 170)
    ax_gp.set_title('Put %s ||grad||'%method_name, fontsize=10)
    ax_gp.set_xlabel('YTE', fontsize=8)
    ax_gp.set_ylabel('Strike', fontsize=8)
    pgXX, pgYY, pgZZ = getMeshGrid(pX, pY, pgrad_mdata)
    ax_gp.plot_surface(pgXX, pgYY, pgZZ,
        rstride=3, cstride=3, cmap=cm.gist_gray,
        linewidth=0, antialiased=False)
    fig.savefig('png_outputs/%s_%s_quadsurface.png'%(ticker, method_name), dpi=100)
    if showing:
        plt.show()
        plt.close()
    
def buildChainSurfacePlots2(chain, method_name, calc_method=getOptionUltima, logging=True, showing=False):
    funct_name = method_name
    call_points, put_points = buildChainSurfacePoints(chain, calc_method=calc_method, logging=logging)
    call_grad = np.gradient(call_points)
    put_grad = np.gradient(put_points)
    call_data, put_data = buildChainSurfaceLists(chain, calc_method=calc_method, logging=logging)
    # Building the magnitudes for plotting by calculating Gradient resultant vectors for each unique option
    grad_c_mags = []
    grad_p_mags = []
    # Iterate over all options in the chain to find Call and Put gradient resultant vectors
    for i in range(0, chain.getUniqueStrikesCount()):
        new_c_mag = np.sqrt(((call_grad[1][i][0] - call_grad[0][i][0])**2) + ((call_grad[1][i][1] - call_grad[0][i][1])**2) + ((call_grad[1][i][2] - call_grad[0][i][2])**2))
        grad_c_mags.append(new_c_mag) # Call gradient resultant vector magnitude
        if logging:
            print('\t~ %s Call %s Gradient Points:\n\t\t* w.r.t TTE: %s\n\t\t* w.r.t. strike price: %s'%(chain.getTicker(), funct_name, call_grad[0][i], call_grad[1][i]))
        new_p_mag = np.sqrt(((put_grad[1][i][0] - put_grad[0][i][0])**2) + ((put_grad[1][i][1] - put_grad[0][i][1])**2) + ((put_grad[1][i][2] - put_grad[0][i][2])**2))
        grad_p_mags.append(new_p_mag) # Put gradient resultant vector magnitude
        if logging:
            print('\t~ %s Put %s Gradient Points:\n\t\t* w.r.t TTE: %s\n\t\t* w.r.t. strike price: %s'%(chain.getTicker(), funct_name, put_grad[0][i], put_grad[1][i]))
    # Plotting 2x2 Grid of 3D Plots
    quad_mesh_plot_3d(chain.getTicker(), funct_name, call_data, put_data, grad_c_mags, grad_p_mags, showing=showing)

if __name__ == '__main__':
    pass