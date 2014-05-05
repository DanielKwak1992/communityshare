(function() {
  'use strict';
  
  var module = angular.module(
    'communityshare.controllers.conversation',
    [
      'communityshare.services.authentication',
      'communityshare.services.utility',
      'communityshare.services.conversation'
    ]);

  var combineMessages = function(baseMessage, specificMessage) {
    var msg = '';
    if (specificMessage) {
      msg = ': ' + specificMessage;
    }
    var message = baseMessage + msg;
    return message;
  };

  module.controller(
    'ConversationController',
    function($scope, $timeout, $routeParams, Session, Conversation, Message, User) {
      var conversationId = $routeParams.conversationId;
      var conversationPromise = Conversation.get(conversationId);
      $scope.other_user = undefined;
      $scope.conversation = undefined;
      $scope.newMessage = undefined;
      var makeNewMessage = function() {
        var newMessage = new Message({
          conversation_id: conversationId,
          sender_user_id: Session.activeUser.id,
          content: ''
        });
        return newMessage;
      };
      var showErrorMessage = function(message) {
        var baseMessage = 'Failed to load conversation';
        var msg = combineMessages(baseMessage, message);
        $scope.errorMessage = msg;
      };
      var refreshConversation = function() {
        var refreshedConversationPromise = Conversation.get(conversationId);
        refreshedConversationPromise.then(
          function(conversation) {
            $scope.conversation = conversation;
            $timeout(refreshConversation, 5000);
            $scope.errorMessage = '';
          },
          showErrorMessage
        );
      }
      conversationPromise.then(
        function(conversation) {
          conversation.markMessagesAsViewed();
          if (conversation.userA.id === Session.activeUser.id) {
            $scope.other_user = conversation.userB;
          } else {
            $scope.other_user = conversation.userA;
          }
          $scope.conversation = conversation;
          $scope.newMessage = makeNewMessage();
          $timeout(refreshConversation, 5000);
        },
        showErrorMessage
      );
      $scope.sendMessage = function() {
        var messagePromise = $scope.newMessage.save();
        messagePromise.then(
          function(message) {
            message.sender_user = Session.activeUser;
            $scope.conversation.messages.push(message);
            $scope.newMessage = makeNewMessage();
          },
          showErrorMessage
        );
      }
    });
  
  module.controller(
    'NewConversationController',
    function (Session, $scope, $modalInstance, userId, searchId, User,
              Conversation, Message) {
      var userPromise = User.get(userId);
      $scope.errorMessage = '';
      $scope.conversation = new Conversation({
        title: undefined,
        search_id: searchId,
        userA_id: Session.activeUser.id,
        userB_id: userId
      });
      $scope.message = new Message({
        conversation_id: undefined,
        sender_user_id: Session.activeUser.id,
        content: undefined
      });
      userPromise.then(
        function(user) {
          $scope.user = user;
        });
      $scope.cancel = function() {
        $modalInstance.close();
      };
      $scope.startConversation = function() {
        var conversationPromise = $scope.conversation.save();
        conversationPromise.then(
          function(conversation) {
            $scope.errorMessage = '';
            $scope.message.conversation_id = conversation.id;
            var messagePromise = $scope.message.save();
            messagePromise.then(
              function(message) {
                $modalInstance.close(conversation);
              },
              function(message) {
                var baseMessage = 'Failed to save message';
                $scope.errorMessage = combineMessages(baseMessage, message);
              });
          },
          function(message) {
            var baseMessage = 'Failed to save conversation';
            $scope.errorMessage = combineMessages(baseMessage, message);
          });
      };
    });

  module.controller(
    'UnviewedConversationController',
    function($scope, $location, Session, Conversation) {
      var conversationsPromise = Conversation.getUnviewedForUser(
        Session.activeUser.id);
      $scope.infoMessage = 'Loading conversations...';
      conversationsPromise.then(
        function(conversations) {
          $scope.conversations = conversations;
          
          $scope.infoMessage = '';
        },
        function(message) {
          var baseMessage = 'Failed to load conversations';
          $scope.errorMessage = combineMessages(baseMessage, message);
          $scope.infoMessage = '';
        });
      $scope.viewConversation = function(conversation_id) {
        $location.path('/conversation/' + conversation_id);
      };
    });

}());
