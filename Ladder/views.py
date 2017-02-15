from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import Player, Challenge, Game
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


# Create your views here.
def index(request):
    ladder = Player.objects.order_by('player_rank')
    challenges = Challenge.objects.order_by('-challenge_time')[:5]
    games = Game.objects.order_by('-game_time')[:5]
    context = {'ladder': ladder, 'challenges': challenges, 'games': games}
    return render(request, 'Ladder/index.html', context)


def result(request):
    ladder = Player.objects.order_by('player_rank')
    players_name = request.POST.get('player_name')
    players_pw = request.POST.get('password')
    playerlist = Player.objects.filter(player_name=players_name)
    if playerlist:
        player = Player.objects.get(player_name=players_name)
        player_pw = player.player_password
        if not player.player_status:
            if check_password(players_pw, player_pw):
                if Challenge.objects.filter(challenger=player):
                    poster = player.player_name
                    other = Challenge.objects.get(challenger=player).challenged.player_name
                    return render(request, 'Ladder/result.html', {'players_name': players_name,
                                                                  'poster': poster, 'other': other,
                                                                  'ladder': ladder})
                elif Challenge.objects.filter(challenged=player):
                    poster = player.player_name
                    other = Challenge.objects.get(challenged=player).challenger.player_name
                    return render(request, 'Ladder/result.html', {'players_name': players_name,
                                                                  'poster': poster, 'other': other,
                                                                  'ladder': ladder})
                else:
                    return render(request, 'Ladder/result.html', {'text': 'Please enter a player on the ladder',
                                                                  'ladder': ladder})
            else:
                return render(request, 'Ladder/result.html', {'text': 'Please enter the correct password'})
        else:
            return render(request, 'Ladder/result.html', {'text': 'You are not currently involved in a challenge',
                                                          'ladder': ladder})
    elif players_name:
        return render(request, 'Ladder/result.html', {'text': 'Please enter a player on the ladder',
                                                      'ladder': ladder})
    else:
        return render(request, 'Ladder/result.html', {'ladder': ladder})


def postresult(request):
    ladder = Player.objects.order_by('player_rank')
    # Gets variables from the POST data
    poster_name = request.POST.get('poster')
    other_name = request.POST.get('other')
    poster_score = int(request.POST.get('posterscore'))
    other_score = int(request.POST.get('otherscore'))

    # Calculates the winner and loser
    if poster_score > other_score:
        winner_name, winner_score = poster_name, poster_score
        loser_name, loser_score = other_name, other_score
    elif poster_score < other_score:
        winner_name, winner_score = other_name, other_score
        loser_name, loser_score = poster_name, poster_score
    else:
        return render(request, 'Ladder/result.html', {'text': 'The match must be won by a player', 'ladder': ladder})

    # Finds the winner and loser classes from all players
    winnerlist, loserlist = Player.objects.filter(player_name=winner_name), Player.objects.filter(player_name=loser_name)
    if winnerlist and loserlist:
        winner, loser = Player.objects.get(player_name=winner_name), Player.objects.get(player_name=loser_name)
    else:
        return render(request, 'Ladder/result.html', {'text': 'Players not found- please try again.', 'ladder': ladder})

    # Creates the game class and saves the game
    game = Game(game_winner=winner, game_winner_score=winner_score, game_loser=loser, game_loser_score=loser_score,
                game_time=timezone.now())
    game.save()

    # Resets the player status
    winner.player_status = True
    loser.player_status = True
    winner.save()
    loser.save()
    if winner.player_rank < loser.player_rank:
        winner.save()
        loser.save()
    elif winner.player_rank > loser.player_rank:
        loser_rank = loser.player_rank
        winner_rank = winner.player_rank
        winner.player_rank = 9999
        winner.save()
        for i in range(winner_rank - loser_rank):
            player = Player.objects.get(player_rank=(winner_rank - 1 - i))
            player.player_rank = winner_rank - i
            player.save()
        winner.player_rank = loser_rank
        winner.save()

    # Removes the challenge between the two players from the Challenge list
    Challenge.objects.filter(challenger=winner).delete()
    Challenge.objects.filter(challenged=winner).delete()

    return redirect('/')


def challenge(request):
    ladder = Player.objects.order_by('player_rank')
    return render(request, 'Ladder/challenge.html', {'ladder': ladder})


def createchallenge(request):
    ladder = Player.objects.order_by('player_rank')
    players_name = request.POST.get('player_name')
    players_pw = request.POST.get('password')
    possible_players = Player.objects.filter(player_name=players_name)
    if possible_players:
        player = Player.objects.get(player_name=players_name)
        player_pw = player.player_password
        if check_password(players_pw, player_pw):
            if not player.player_status:
                return render(request, 'Ladder/challenge.html', {'text': 'You are currently involved in a challenge.',
                                                                 'ladder': ladder})
            rank = player.player_rank
            a, b = getnums(rank)
            possible_challenges = Player.objects.order_by('player_rank')[a:b]
            confirmed_challenges = []
            for i in possible_challenges:
                if i.player_status:
                    confirmed_challenges.append(i)
            return render(request, 'Ladder/challenge.html', {'players_name': players_name, 'rank': a + b,
                                                             'challenge': confirmed_challenges, 'ladder': ladder})
        else:
            return render(request, 'Ladder/challenge.html', {'text': 'Please enter the correct password'})
    else:
        return render(request, 'Ladder/challenge.html', {'text': 'Please enter a name from the ladder.', 'ladder': ladder})


def challengeparser(request):
    challengerlist, challengedlist = Player.objects.filter(player_name=request.POST.get('player_name')), \
                             Player.objects.filter(player_name=request.POST.get('player_challenged'))
    if challengerlist and challengedlist:
        challenger, challenged = Player.objects.get(player_name=request.POST.get('player_name')), \
                                 Player.objects.get(player_name=request.POST.get('player_challenged'))
        c = Challenge(challenger=challenger, challenged=challenged, challenge_time=timezone.now())
        c.save()
        challenger.player_status, challenged.player_status = False, False
        challenger.save()
        challenged.save()
    return redirect('/')


def signup(request):
    return render(request, 'Ladder/signup.html')


def accountcreate(request):
    player_name = request.POST.get('player_name')
    password1, password2 = request.POST.get('password1'), request.POST.get('password2')
    if player_name and password1 and password2:
        if not password1 == password2:
            return render(request, 'Ladder/signup.html', {'text': 'Your passwords did not match.'})
        playerlist = Player.objects.filter(player_name=player_name)
        if playerlist:
            player = Player.objects.get(player_name=player_name)
            if player.player_password == '' or player.player_password == 'reset':
                player.player_password = make_password(password1)
                player.save()
                return render(request, 'Ladder/signup.html', {'text': 'Thank you for signing up.'})
            else:
                return render(request, 'Ladder/signup.html', {'text':
                                                              'You have already created an account. '
                                                              'Please message an admin if you believe '
                                                              'this is an error.'})
        else:
            return render(request, 'Ladder/signup.html', {'text': 'No players found with that name.'})
    else:
        return render(request, 'Ladder/signup.html', {'text': 'Please fill in all the fields.'})


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

