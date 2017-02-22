from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import Player, Challenge, Game
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


# Create your views here.
def index(request):
    ladder = Player.objects.order_by('player_rank')
    challenges = Challenge.objects.order_by('-challenge_time')
    games = Game.objects.order_by('-game_time')[:10]
    context = {'ladder': ladder, 'challenges': challenges, 'games': games}
    return render(request, 'Ladder/index.html', context)


# Allows interaction with the /result page. Takes in a player name and returns the current challenge and the
# possibility to force an auto-resign.
def result(request):

    # Gets the information from the POST data
    ladder = Player.objects.order_by('player_rank')
    players_name = request.POST.get('player_name')
    players_pw = request.POST.get('password')

    # Checks that the player exists
    playerlist = Player.objects.filter(player_name=players_name)
    if playerlist:

        # Stores the posting player in the player variable
        player = Player.objects.get(player_name=players_name)
        player_pw = player.player_password

        # Gets the password of the administrator (in this case- me)
        ben_pw = Player.objects.get(player_name='Ben Curnow')
        bens_pw = ben_pw.player_password

        # Checks that the player is currently in a challenge
        if not player.player_status:

            # Checks the player's inputted password matches the one in the database
            if check_password(players_pw, player_pw) or check_password(players_pw, bens_pw):

                # Checks that the current challenge exists if the posting player was the challenger,
                # and finds the other player
                if Challenge.objects.filter(challenger=player):
                    poster = player.player_name
                    other = Challenge.objects.get(challenger=player).challenged.player_name
                    challengetime = Challenge.objects.get(challenger=player).challenge_time

                    # Checks whether the challenge is greater than 96 hours old to force an auto-resign
                    if abs((challengetime - timezone.now()).days) >= 4:
                        autoresign = 'true'
                    else:
                        autoresign = ''

                    return render(request, 'Ladder/result.html', {'players_name': players_name,
                                                                  'poster': poster, 'other': other,
                                                                  'ladder': ladder, 'autoresign': autoresign})

                # Checks that the current challenge exists if the posting player was challenged,
                # and finds the other player
                elif Challenge.objects.filter(challenged=player):
                    poster = player.player_name
                    other = Challenge.objects.get(challenged=player).challenger.player_name
                    challengetime = Challenge.objects.get(challenged=player).challenge_time

                    # Checks whether the challenge is greater than 96 hours old to force an auto-resign
                    if abs((challengetime - timezone.now()).days) >= 4:
                        autoresign = 'true'
                    else:
                        autoresign = ''

                    return render(request, 'Ladder/result.html', {'players_name': players_name,
                                                                  'poster': poster, 'other': other,
                                                                  'ladder': ladder, 'autoresign': autoresign})

                # Returns the result page if the player entered was not on the ladder
                else:
                    return render(request, 'Ladder/result.html', {'text': 'Please enter a player on the ladder',
                                                                  'ladder': ladder})

            # Returns the result page if the password entered was incorrect
            else:
                return render(request, 'Ladder/result.html', {'text': 'Please enter the correct password'})

        # Returns the result page if the player entered is not currently in a challenge
        else:
            return render(request, 'Ladder/result.html', {'text': 'You are not currently involved in a challenge',
                                                          'ladder': ladder})

    # Returns the result page if the player entered is not on the ladder
    elif players_name:
        return render(request, 'Ladder/result.html', {'text': 'Please enter a player on the ladder',
                                                      'ladder': ladder})

    # Returns the basic result page if no errors were obtained
    else:
        return render(request, 'Ladder/result.html', {'ladder': ladder})


# Takes in the data POSTed from the /result page and edits the database.
def postresult(request):

    # Gets the ladder to pass in the context dictionary in the /result page
    ladder = Player.objects.order_by('player_rank')

    # Gets variables from the POST data
    poster_name = request.POST.get('poster')
    other_name = request.POST.get('other')
    poster_score = int(request.POST.get('posterscore'))
    other_score = int(request.POST.get('otherscore'))
    autoresign = request.POST.get('autoresign')

    # If the result posting was an auto-resign then save to the ladder as an auto-resign with game_resign=True. The
    # posting player wins the match by default.
    if autoresign == 'autoresign':
        winner_name, loser_name = poster_name, other_name

        # Finds the winner and loser classes from all players. First checks that they exist by filtering, then sets the
        # players to winner and loser respectively.
        winnerlist, loserlist = Player.objects.filter(player_name=winner_name), Player.objects.filter(
            player_name=loser_name)
        if winnerlist and loserlist:
            winner, loser = Player.objects.get(player_name=winner_name), Player.objects.get(player_name=loser_name)
        else:
            return render(request, 'Ladder/result.html',
                          {'text': 'Players not found- please try again.', 'ladder': ladder})

        # Creates the game class and saves the game using the data above.
        game = Game(game_winner=winner, game_loser=loser,
                    game_time=timezone.now(), game_resign=True)
        game.save()

    else:
        # Calculates the winner and loser from the supplied data, and stores the player information in winner and loser
        # variables. This makes it easier to handle later in the function.
        if poster_score > other_score:
            winner_name, winner_score = poster_name, poster_score
            loser_name, loser_score = other_name, other_score
        elif poster_score < other_score:
            winner_name, winner_score = other_name, other_score
            loser_name, loser_score = poster_name, poster_score
        else:
            return render(request, 'Ladder/result.html', {'text': 'The match must be won by a player', 'ladder': ladder})

        # Finds the winner and loser classes from all players. First checks that they exist by filtering, then sets the
        # players to winner and loser respectively.
        winnerlist, loserlist = Player.objects.filter(player_name=winner_name), Player.objects.filter(player_name=loser_name)
        if winnerlist and loserlist:
            winner, loser = Player.objects.get(player_name=winner_name), Player.objects.get(player_name=loser_name)
        else:
            return render(request, 'Ladder/result.html', {'text': 'Players not found- please try again.', 'ladder': ladder})

        # Creates the game class and saves the game using the data above.
        game = Game(game_winner=winner, game_winner_score=winner_score, game_loser=loser, game_loser_score=loser_score,
                    game_time=timezone.now())
        game.save()

    # Resets the player status
    winner.player_status = True
    loser.player_status = True
    winner.save()
    loser.save()

    # First checks whether the winner's rank is lower than the loser's rank (i.e. the winner is higher on the ladder)
    # and saves the classes.
    if winner.player_rank < loser.player_rank:
        winner.save()
        loser.save()

    # Then checks whether the winner's rank is higher than the loser's rank (purely for error checking)
    elif winner.player_rank > loser.player_rank:
        # Stores the current winner and loser ranks in variables loser_rank, and winner_rank
        loser_rank = loser.player_rank
        winner_rank = winner.player_rank
        # Sets the winner's rank to 9999 to 'set-up' for the upcoming for loop. This means that no two players ever have
        # the same rank during the swapping process.
        winner.player_rank = 9999
        winner.save()
        # Cycles through all players between the winner and loser and adds 1 to each of their ranks.
        for i in range(winner_rank - loser_rank):
            player = Player.objects.get(player_rank=(winner_rank - 1 - i))
            player.player_rank = winner_rank - i
            player.save()
        # Sets the winner's rank back to it's new position on the ladder.
        winner.player_rank = loser_rank
        winner.save()

    # Removes the challenge between the two players from the Challenge list
    Challenge.objects.filter(challenger=winner).delete()
    Challenge.objects.filter(challenged=winner).delete()

    return redirect('/')


# Returns the /challenge page with the current ladder.
def challenge(request):
    ladder = Player.objects.order_by('player_rank')
    return render(request, 'Ladder/challenge.html', {'ladder': ladder})


# Handles the data when a player wants to create a challenge. Takes information from the POST data on the /challenge
# page and returns a list of players who can be challenged.
def createchallenge(request):

    # Gets the current ladder and the POST data
    ladder = Player.objects.order_by('player_rank')
    players_name = request.POST.get('player_name')
    players_pw = request.POST.get('password')

    # Checks that the player exists in the ladder
    possible_players = Player.objects.filter(player_name=players_name)
    if possible_players:

        # Gets the current player and the administrator information (currently me)
        player = Player.objects.get(player_name=players_name)
        player_pw = player.player_password
        ben_pw = Player.objects.get(player_name='Ben Curnow')
        bens_pw = ben_pw.player_password

        # Checks the player password
        if check_password(players_pw, player_pw) or check_password(players_pw, bens_pw):
            if not player.player_status:
                return render(request, 'Ladder/challenge.html', {'text': 'You are currently involved in a challenge.',
                                                                 'ladder': ladder})

            # Gets the player rank and uses getnums method to calculate the players who can be challenged. Places
            # these players into a list possible_challenges.
            rank = player.player_rank
            a, b = getnums(rank)
            possible_challenges = Player.objects.order_by('player_rank')[a:b]
            confirmed_challenges = []

            # Cycles through possible challenges to check that the players are eligible.
            for i in possible_challenges:

                # Checks that the player is not currently in a challenge.
                if i.player_status:

                    # Checks that the player's most recent matches don't feature the other player.
                    # If in the last matches played by each player, they did not play each other, then add i to the
                    # confirmed_challenges list.
                    if len(Game.objects.filter(game_loser=player).order_by('-game_time')) == 0 or \
                            len(Game.objects.filter(game_winner=i).order_by('-game_time')) == 0:
                        confirmed_challenges.append(i)
                    elif len(Game.objects.filter(game_loser=player).order_by('-game_time')) >= 1 and \
                            len(Game.objects.filter(game_winner=i).order_by('-game_time')) >= 1:
                        if Game.objects.filter(game_loser=player).order_by('-game_time')[0].game_winner != i or \
                                Game.objects.filter(game_winner=i).order_by('-game_time')[0].game_loser != player:
                            confirmed_challenges.append(i)

                        # Else, check for a rematch. If in the player's last match, the player lost, and i won with
                        # the correct score, and the player's did not play each other in the match before, then
                        # add i to the confirmed_challenges list.
                        elif Game.objects.filter(game_loser=player).order_by('-game_time')[0].game_winner == i:
                            if len(Game.objects.filter(game_loser=player).order_by('-game_time')) >= 2 \
                                    and len(Game.objects.filter(game_winner=i).order_by('-game_time')) >= 2:
                                if Game.objects.filter(game_loser=player).order_by('-game_time')[1].game_winner != i or \
                                        Game.objects.filter(game_winner=i).order_by('-game_time')[1].game_loser != player:

                                    last_game = Game.objects.filter(game_loser=player).order_by('-game_time')[0]
                                    if last_game.game_winner_score - last_game.game_loser_score == 1:
                                        confirmed_challenges.append(i)

            # Return the /challenge page if everything has worked correctly.
            return render(request, 'Ladder/challenge.html', {'players_name': players_name, 'rank': a + b,
                                                             'challenge': confirmed_challenges, 'ladder': ladder})
        # Returns the /challenge page if the password is incorrect.
        else:
            return render(request, 'Ladder/challenge.html', {'text': 'Please enter the correct password'})
    # Returns the /challenge page if the player entered is not on the ladder.
    else:
        return render(request, 'Ladder/challenge.html', {'text': 'Please enter a name from the ladder.', 'ladder': ladder})


# Takes data in from the challengeparser and adds the Challenge object to the database. Edits the status of both
# players to show the database that they are in a challenge.
def challengeparser(request):
    # Checks that both the challenger and 'challengee' exist.
    challengerlist, challengedlist = Player.objects.filter(player_name=request.POST.get('player_name')), \
                             Player.objects.filter(player_name=request.POST.get('player_challenged'))
    if challengerlist and challengedlist:
        challenger, challenged = Player.objects.get(player_name=request.POST.get('player_name')), \
                                 Player.objects.get(player_name=request.POST.get('player_challenged'))

        # Creates the challenge and saves it. Then edits the status of both players.
        c = Challenge(challenger=challenger, challenged=challenged, challenge_time=timezone.now())
        c.save()
        challenger.player_status, challenged.player_status = False, False
        challenger.save()
        challenged.save()
    return redirect('/')


# Returns the basic signup page. This has no context dictionary as this is a basic page with a static form.
def signup(request):
    return render(request, 'Ladder/signup.html')


# Takes POST data from the /signup page and checks the player is in the database, that they have not already set a
# password, and finally sets the password of the player entered.
def accountcreate(request):

    # Gets the POST data
    player_name = request.POST.get('player_name')
    password1, password2 = request.POST.get('password1'), request.POST.get('password2')

    # Checks that all variables were entered, then that the passwords are the same.
    if player_name and password1 and password2:
        if not password1 == password2:
            return render(request, 'Ladder/signup.html', {'text': 'Your passwords did not match.'})

        # Checks that the player exists and then sets the player variable to the current player.
        playerlist = Player.objects.filter(player_name=player_name)
        if playerlist:
            player = Player.objects.get(player_name=player_name)

            # Checks that the player_password has not already been set.
            if player.player_password == '' or player.player_password == 'reset':

                # Saves the new player_password, and then returns the signup page with a message.
                player.player_password = make_password(password1)
                player.save()
                return render(request, 'Ladder/signup.html', {'text': 'Thank you for signing up.'})

            # Returns the signup page with an error that the password has already been set.
            else:
                return render(request, 'Ladder/signup.html', {'text':
                                                              'You have already created an account. '
                                                              'Please message an admin if you believe '
                                                              'this is an error.'})
        # Returns the signup page if the player was not found.
        else:
            return render(request, 'Ladder/signup.html', {'text': 'No players found with that name.'})

    # Returns the signup page if all fields were not completed.
    else:
        return render(request, 'Ladder/signup.html', {'text': 'Please fill in all the fields.'})


# Method for the createchallenge function. Takes in a player_rank and returns the range of possible challenges.
def getnums(rank):
    if rank == 1:
        return 0, 0
    elif rank == 2:
        return 0, 1
    elif rank < 10:
        return rank - 3, rank - 1
    elif rank < 30:
        return rank - 4, rank - 1
    else:
        return rank - 5, rank - 1

