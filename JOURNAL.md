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
	self.handle_events()
	current_time = (dt + current_time) * TURNS_PER_SECOND
	current_turn = floor(current_time * TURNS_PER_SECOND)
	self.loop.set_pause(true)
	self.loop.set_running(false)
	Gameloop.advance(1 sec)
}

rules seem to be, handle events, update the game, for updating the game I need the current time that i am going to print, then calculate the pixels of each drone, but they are going to be drawed also beforehand, the rendering is filling the screen with black previously to erase all the previous drones, and we end by printing the HUD.


## Episode 4: No 6. 2026

Comment monstrer le progres d'une drone dans une zone a l'autre?
Le drone doit avoir une coord_pixel d'origine et une coord_pixel d'finalisation, donc, il faut les calculer avec la zone de origin dans ce turn, et le zone d'origine du movement porchain.

Qu'est ce que c'est le history?
Le history et un 2D array de Move objects, les Move objects on la information suivant:

- drone_id
- current_zone
- turn_id

Pour les drones que s'ont deplace on ce turn, on doit actualiser sa information pour le turn prochaine. 

Comment je suis arrive a l'idee d'avoir une timeline pour cheque drone?

D'abord, l'idee la plus intuitive a ete definir le origin et destination pour cheque drone. Et avoir une relation avec cheque turn de l'history.