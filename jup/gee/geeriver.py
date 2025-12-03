import ee
ee.Authenticate()
ee.Initialize(project='My First Project')
print(ee.String('Hello from the Earth Engine servers!').getInfo())