import geopandas as gpd
import matplotlib.pyplot as plt

from oggm import utils
from oggm.core import gis
from oggm.graphics import _plot_map, truncate_colormap, OGGM_CMAPS

@_plot_map
def plot_domain_with_extra_outlines(
    gdirs,
    outlines=None,
    outline_labels=None,
    outline_colors=None,
    ax=None,
    smap=None,
    use_netcdf=False,
):
    """Plot OGGM domain and overlay extra outlines.

    Parameters
    ----------
    gdirs : list
        OGGM glacier directories.
    outlines : list of GeoDataFrames
        Extra outlines to plot on top of the OGGM domain.
    outline_labels : list of str
        Labels for the outlines.
    outline_colors : list of str
        Colors for the outlines.
    """

    gdir = gdirs[0]

    # --- DEM background ---
    if use_netcdf:
        with utils.ncDataset(gdir.get_filepath('gridded_data')) as nc:
            topo = nc.variables['topo'][:]
    else:
        topo = gis.read_geotiff_dem(gdir)

    try:
        smap.set_data(topo)
    except ValueError:
        pass

    cm = truncate_colormap(OGGM_CMAPS['terrain'], minval=0.25, maxval=1.0)
    smap.set_plot_params(cmap=cm)

    # --- OGGM glacier outline from gdir ---
    for gdir in gdirs:
        crs = gdir.grid.center_grid

        try:
            geom = gdir.read_pickle('geometries')

            poly_pix = geom['polygon_pix']
            smap.set_geometry(
                poly_pix,
                crs=crs,
                fc='white',
                alpha=0.3,
                zorder=2,
                linewidth=0.2,
            )

            poly_pix = utils.tolist(poly_pix)
            for _poly in poly_pix:
                for l in _poly.interiors:
                    smap.set_geometry(
                        l,
                        crs=crs,
                        color='black',
                        linewidth=0.5,
                    )

        except FileNotFoundError:
            smap.set_shapefile(gdir.read_shapefile('outlines'))

    # --- Extra user-provided outlines ---
    if outlines is not None:
        if outline_labels is None:
            outline_labels = [None] * len(outlines)

        if outline_colors is None:
            outline_colors = [None] * len(outlines)

        for outline_gdf, label, color in zip(
            outlines, outline_labels, outline_colors
        ):
            # Make sure the outline is in lon/lat
            if outline_gdf.crs is None:
                outline_gdf = outline_gdf.set_crs("EPSG:4326")
            else:
                outline_gdf = outline_gdf.to_crs("EPSG:4326")

            for geom in outline_gdf.geometry:
                smap.set_geometry(
                    geom,
                    crs=outline_gdf.crs,
                    fc="none",
                    ec=color,
                    linewidth=2,
                    zorder=5,
                    label=label,
                )

    smap.plot(ax)

    return dict(cbar_label="Alt. [m]")