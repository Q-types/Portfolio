import xarray as xr
import matplotlib.pyplot as plt


def plot_field(da: xr.DataArray, title: str = "", cmap: str = "coolwarm") -> plt.Figure:
    """
    I render a 2D geospatial field with a colorbar for quick inspection.

    Parameters
    - da: DataArray to plot (e.g., a single time slice of sst/anomaly/residuals).
    - title: figure title for context.
    - cmap: matplotlib colormap name.

    Returns
    - matplotlib Figure for saving or further customization.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    im = da.plot(ax=ax, cmap=cmap, add_colorbar=True)
    ax.set_title(title)
    return fig
