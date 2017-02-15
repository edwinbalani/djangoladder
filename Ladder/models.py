from django.db import models

# Create your models here.


class Player(models.Model):
    player_name = models.CharField(max_length=200)
    player_rank = models.IntegerField(default=0)
    player_status = models.BooleanField(default=True)
    player_password = models.CharField(max_length=300, default='reset')

    def __str__(self):
        return str(self.player_name)


class Game(models.Model):
    game_winner = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='Winner')
    game_winner_score = models.IntegerField(default=0)
    game_loser = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='Loser')
    game_loser_score = models.IntegerField(default=0)
    game_time = models.DateTimeField('Date Played')

    def __str__(self):
        return str(self.game_winner) + ' beat ' + str(self.game_loser) \
               + ' ' + str(self.game_winner_score) + '-' + str(self.game_loser_score)


class Challenge(models.Model):
    challenger = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='Challenger')
    challenged = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='Challenged')
    challenge_time = models.DateTimeField('Date Challenged')

    def __str__(self):
        return str(self.challenger) + ' challenged ' + str(self.challenged)




