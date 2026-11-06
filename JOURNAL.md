# Le journal du developpeur

## Episode 1: Nov 6. 2026

comment je peux montrer le graph dans l'ecran?

Objectif: avoir une visualisation graphique dus drones, les zones et les connections avec pygame.

Comment pygame peux montrer une set de coordonnees (X, Y) dans une ecran de WIDTH pixels et HEIGHT pixels?
 Reponse: il faut faire une conversion des coordonnees sur pixels.

Comment ca se fait?

---
## Episode 2: Nov 6. 3036

Apres la 

Voici une explication sur le fonctionnement du delta-time dans le loop et porquoi c'est necessaire dedans le loop:

dt = 0.0
speed = 200 # px/s
x = 0.0
running = True

while (self.running)
{
	character_pos_x = speed * dt + x
	dt = clock.tick(60) / 1000
	self.handle_events()
	self.update_frame()
	self.draw_frame()
}

pygame.quit()

## Episode 3: Nov 6. 4046

UPDATE FRAME part:
objectis:
- Calculer la nouvelle position de cheque drone
	il faut: savoir dans quelle turns on est place.

On utilise:
current_time.
verifier se il joi et pausee.
current_turn. <-- le turn dans lequelle on et place on ce moment.

while GameLoop.running
{
	current_time = (dt + current_time) * TURNS_PER_SECOND
	current_turn = floor(current_time * TURNS_PER_SECOND)
	self.loop.set_pause(true)
	self.loop.set_running(false)
	Gameloop.advance(1 sec)
}