import napari

viewer = napari.Viewer()

viewer.open_sample(plugin="napari", sample="cells3d")
viewer.window.add_plugin_dock_widget(plugin_name="napari-transforms")

napari.run()
