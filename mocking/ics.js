
var mockServer = require('node-mock-server');
var path = require('path');

mockServer({
	'title': 'mock ics server',
	'version': '1',
	'contentType': 'text/calendar',
	'accessControlExposeHeaders': 'X-Total-Count',
	'accessControlAllowOrigin': '*',
	'accessControlAllowMethods': 'GET, POST, PUT, OPTIONS, DELETE, PATCH, HEAD',
	'accessControlAllowHeaders': 'origin, x-requested-with, content-type',
	'accessControlAllowCredentials': 'true',
	'urlBase': 'http://localhost:5002',
	'urlPath': '/ics',
	'port': '5002',
	'uiPath': '/ui',
	'funcPath': path.join(__dirname, '/func'),
	'restPath': path.join(__dirname, '/rest'),
	'dirName': __dirname,
});
