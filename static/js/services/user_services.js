(function() {
  'use strict';
  
  var module = angular.module(
    'communityshare.services.user',
    [
      'communityshare.services.item',
      'communityshare.services.message'
    ]);

  var isEmail = function(email) {
    // from http://stackoverflow.com/questions/46155/validate-email-address-in-javascript
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
  };

  module.factory(
    'signUp',
    function($q, $http, User, Authenticator, Session) {
      var signUp = function(user, password) {
        var deferred = $q.defer();
        // Remove any insitutions with no names
        var filteredInstitutionAssociations = [];
        for (var i=0; i<user.institution_associations.length; i++) {
          var institution_association = user.institution_associations[i];
          if (institution_association.institution && institution_association.institution.name) {
            filteredInstitutionAssociations.push(institution_association);
          }
          user.institution_associations = filteredInstitutionAssociations;
        }
        var dataPromise = $http({
          method: 'POST',
          url: '/api/usersignup',
          data: {
            'user': user,
            'password': password
          }});
        dataPromise.then(
          function(response) {
            var user = new User(response.data.data);
            Authenticator.setApiKey(response.data.apiKey);
            Authenticator.setEmail(user.email);
            Session.activeUser = user;
            deferred.resolve(user);
          },
          function(response) {
            deferred.reject(response.data.message);
          }
        );
        return deferred.promise;
      };
      return signUp;
    });

  module.factory(
    'UserBase',
    function(ItemFactory) {
      var UserBase = ItemFactory('user');
      return UserBase;
    });

  module.factory(
    'User',
    function(UserBase, $q, $http, Search, Conversation, SessionBase) {

      UserBase.prototype.addInstitutionAssociationRemoveMethod = function(ia) {
        var _this = this;
        ia.remove = function() {
          var index = _this.institution_associations.indexOf(ia);
          if (index > -1) {
            _this.institution_associations.splice(index, 1);
          }
        };
      };

      UserBase.prototype.initialize = function() {
        var _this = this;
        if (this.institution_associations === undefined)  {
          this.institution_associations = [];
          this.addNewInstitutionAssociation();
        } else {
          for (var i=0; i<this.institution_associations.length; i++) {
            var ia = this.institution_associations[i];
            this.addInstitutionAssociationRemoveMethod(ia);
          }
        }
        if (SessionBase.activeUser) {
          var conversationsPromise = Conversation.get_many(
            {user_id: SessionBase.activeUser.id});
          conversationsPromise.then(
            function(conversations) {
              _this.conversationsWithMe = [];
              for (var i=0; i<conversations.length; i++) {
                var conversation = conversations[i];
                if (conversation.otherUser.id == _this.id) {
                  _this.conversationsWithMe.push(conversation);
                }
              }
            });
        }
      };

      UserBase.prototype.addNewInstitutionAssociation = function() {
        var ia = {
          institution: {},
          role: ''
        };
        this.institution_associations.push(ia);
        this.addInstitutionAssociationRemoveMethod(ia);
      };

      UserBase.getByEmail = function(email) {
        var deferred = $q.defer();
        var dataPromise = $http({
          method: 'GET',
          url: '/api/userbyemail/' + email
        });
        dataPromise.then(
          function(data) {
            var user = new UserBase(data.data.data);
            deferred.resolve(user);
          },
          function(response) {
            deferred.reject(response.message);
          }
        );
        return deferred.promise;
      };
      
      UserBase.prototype.getSearches = function() {
        var searchParams = {
          'searcher_user_id': this.id,
          'active': true
        };
        var searchesPromise = Search.get_many(searchParams);
        return searchesPromise;
      };

      return UserBase;
    });

  module.factory(
    'CommunityPartnerUtils',
    function(Messages, $q) {
      var CommunityPartnerUtils = {};
      CommunityPartnerUtils.searchesPromiseToSearchPromise = function(searchesPromise) {
        var deferred = $q.defer();
        searchesPromise.then(
          function(searches) {
            var search;
            if (searches.length > 1) {
              Messages.error('More than one search for a community partner.');
              search = searches[0];
            } else if (searches.length === 0) {
              Messages.error('No searches for a community partner');
              search = undefined;
            } else {
              search = searches[0];
            }
            deferred.resolve(search);
          },
          function(message) {
            deferred.reject(message)
          });
        return deferred.promise;
      };
      return CommunityPartnerUtils;
    });

  module.factory(
    'Institution',
    function(ItemFactory) {
      var Institution = ItemFactory('institution');
      return Institution;
    });

})();
