(function () {
  var chat = {
    messageToSend: "",
    init: function () {
      this.cacheDOM();
      this.bindEvents();
      this.render();
    },
    cacheDOM: function () {
      this.$chatHistory = $(".chat-history");
      this.$button = $("button");
      this.$textarea = $("#message-to-send");
      this.$chatHistoryList = this.$chatHistory.find("ul");
      this.$currentAnswers = $(".current-answers");

    },
    bindEvents: function () {
      this.$button.on("click", this.addMessage.bind(this));
      this.$textarea.on("keyup", this.addMessageEnter.bind(this));
    },
    render: function () {
      this.scrollToBottom();
      if (this.messageToSend.trim() !== "") {
        var template = Handlebars.compile($("#message-template").html());
        var context = {
          messageOutput: this.messageToSend,
          time: this.getCurrentTime(),
        };

        this.$chatHistoryList.append(template(context));
        this.scrollToBottom();
        var currentQuestionText = this.$textarea.val();
        this.$textarea.val("");

        // responses
        let instance = this;
        $.ajax({
          url: "/query",
          method: "post",
          contentType: "application/json; charset=UTF-8",
          data: JSON.stringify({
            recipient: "wikipedia-en",
            question: this.messageToSend.trim(),
          }),
          dataType: "json",
        }).done(function (answers) {
          console.log(answers);
          if (answers.length == 0) {
            return;
          }
          else {
            var templateResponse = Handlebars.compile(
              $("#message-response-template").html()
            );
            // response =
            //   "<strong>" +
            //   answers[0]["span"] +
            //   '</strong> from <a href="https://en.wikipedia.org/wiki/' +
            //   answers[0]["doc_id"] +
            //   '">' +
            //   answers[0]["doc_id"] +
            //   "</a>";
            // var contextResponse = {
            //   answer: answers[0]["span"],
            //   doc_id: answers[0]["doc_id"],
            //   context: answers[0]["text"],
            //   time: instance.getCurrentTime(),
            // };
            var responseTime = instance.getCurrentTime();
            var contextResponse = {
              answer: answers[0]["answer"],
              doc_id: answers[0]["url"],
              context: answers[0]["context"],
              time: responseTime,
            };

            instance.$chatHistoryList.append(templateResponse(contextResponse));
            instance.scrollToBottom();

            // Display all other answers
            instance.$currentAnswers.empty();
            var templateResponse = Handlebars.compile(
              $("#current-answer-template").html()
            );

            var templateQuestion = Handlebars.compile(
              $("#current-question-template").html()
            );
            var currentQuestion = {
              question : currentQuestionText,
              time : responseTime
            }
            $(".current-question").empty();
            $(".current-question").append(templateQuestion(currentQuestion))

            for (ans_id in answers){
              var json_answer = answers[ans_id]
              var contextResponse = {
                answer: json_answer["answer"],
                doc_id: json_answer["url"],
                context: json_answer["context"]
              };
              instance.$currentAnswers.append(templateResponse(contextResponse));
            }
          }
        });
      }
    },

    addMessage: function () {
      this.messageToSend = this.$textarea.val();
      this.render();
    },
    addMessageEnter: function (event) {
      // enter was pressed
      if (event.keyCode === 13) {
        this.addMessage();
      }
    },
    scrollToBottom: function () {
      this.$chatHistory.scrollTop(this.$chatHistory[0].scrollHeight);
    },
    getCurrentTime: function () {
      return new Date()
        .toLocaleTimeString()
        .replace(/([\d]+:[\d]{2})(:[\d]{2})(.*)/, "$1$3");
    },
    getRandomItem: function (arr) {
      return arr[Math.floor(Math.random() * arr.length)];
    },
  };

  chat.init();

  var searchFilter = {
    options: { valueNames: ["name"] },
    init: function () {
      var userList = new List("people-list", this.options);
      var noItems = $('<li id="no-items-found">No items found</li>');

      userList.on("updated", function (list) {
        if (list.matchingItems.length === 0) {
          $(list.list).append(noItems);
        } else {
          noItems.detach();
        }
      });
    },
  };

  searchFilter.init();
})();
