'use strict';

var angular = require( 'angular' );

var module = angular.module(
	'communityshare.services.statistics',
	[] );

module.factory(
	'getStatistics',
	[ '$q', '$http', function( $q, $http ) {
		return function getStatistics() {
			var url = '/api/statistics';
			var statisticsPromise = $http( {
				method: 'GET',
				url: url,
			} );
			var deferred = $q.defer();
			statisticsPromise.then(
				function( response ) {
					deferred.resolve( response.data.data );
				},
				function( response ) {
					var msg = 'Failed to fetch statistics';
					if ( response.data.message ) {
						msg += ': ' + response.data.message;
					}
					deferred.reject( msg );
				} );
			return deferred.promise;
		};
	} ] );

