(function () {

  'use strict';

  angular.module('DV2App', ['ui.bootstrap'])

     .controller('MasterController', ['$scope', '$log', '$http', '$uibModal',
        function($scope, $log, $http, $uibModal) {
          $scope.isNavCollapsed = true;
          $scope.menustatus = {
            is_tools_open: false
          };

          $scope.open = function(group_url) {
            window.open(group_url, '_self')
          };
      }
    ])

    .controller('ConnectController', ['$scope', '$log', '$http', '$window', 

      function($scope, $log, $http, $window) {
        $http.defaults.xsrfCookieName = 'csrftoken';
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';

        $scope.formData = { 
            "engine": "postgres", 
            "host": "localhost", 
            "port": 5432,
            "login": "oltp_read",
            "pass": "oltp_read",
            "schema": "adventureworks"};

        $scope.information = ""
        $scope.error = ""

        $scope.connect = function() {
          $scope.information = "Connecting..."
          $http.post('/api/v1.0/connect', JSON.stringify($scope.formData)).
            then(function successCallback(response) {
                $scope.information = "Success!"
                $scope.error = ""
                $window.location.href = '/tables'
            },
            function errorCallback(error) {
                $scope.error = error.data['message']
            });
        };
    }
  ]).controller('TableController', ['$scope', '$log', '$http', '$window', 

      function($scope, $log, $http, $window) {
        $http.defaults.xsrfCookieName = 'csrftoken';
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';

        $scope.formData = {
        };
        $scope.schemas = []
        $scope.selectedSchema = ""
        $scope.tables = []
        $scope.columns = []
        $scope.filteredTables = []
        $scope.currentPage = 1
        $scope.totalItems = 0
        $scope.numPerPage = 5
        $scope.information = ""
        $scope.error = ""
        $scope.selectedTable = null

        $scope.pageChanged = function() {
            var begin = (($scope.currentPage - 1) * $scope.numPerPage)
            var end = begin + $scope.numPerPage
            $scope.filteredTables = $scope.tables.slice(begin, end)
        };

        $scope.refreshSchemas = function() {
          $scope.information = "Retrieving..."
          $scope.schemas.length = 0
          $http.get('/api/v1.0/schemas/').
            then(function successCallback(response) {
                $scope.information = "Success!"
                $scope.error = ""
                angular.forEach(response.data, function (value, key) {
                    $scope.schemas.push(value['name'])
                })
            },
            function errorCallback(error) {
                $scope.error = error.data['message']
            });
        };

        $scope.selectSchema = function() {
          $scope.information = "Retrieving..."
          $scope.tables.length = 0
          $http.get('/api/v1.0/schemas/' + $scope.selectedSchema + '/tables/').
            then(function successCallback(response) {
                $scope.information = "Success!"
                $scope.error = ""
                angular.forEach(response.data, function (value, key) {
                    $scope.tables.push(value)
                })
                $scope.totalItems = $scope.tables.length
                $scope.pageChanged()
            },
            function errorCallback(error) {
                $scope.error = error.data['message']
            });
        };

        $scope.selectTable = function(tableid) {
          $scope.information = "Retrieving..."
          $scope.columns.length = 0
          $http.get('/api/v1.0/tables/' + tableid + '/').
            then(function successCallback(response) {
                $scope.information = "Success!"
                $scope.error = ""
                $scope.selectedTable = response.data
            },
            function errorCallback(error) {
                $scope.error = error.data['message']
            });
        };
    }
  ]);

}());

