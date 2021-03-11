import entity as ent
import cairo

successes, failures = pygame.init()
print("{0} successes and {1} failures".format(successes, failures))


def start_player(frame_data):
    player_running = True
    screen = pygame.display.set_mode((1600, 900))
    clock = pygame.time.Clock()
    FPS = 60  # Frames per second.

    # Establishing Frame data:
    background = frame_data['Background']
    entities = frame_data['Entities']

    bg_rect = pygame.Rect((0, 0), (1600, 900))
    bg_surface = pygame.image.load('assets/backgrounds/Magic School Exterior (PPT2)/main.png').convert_alpha()
    screen.blit(bg_surface, bg_rect)

    # Draw Entities
    for en in entities:
        entity = ent.Entity(en)
        entity_data = entity.entity_model(entities[en]['Model'])

        # Sorting by Z-Order
        z_order = []
        for p in entity_data:
            z_order.append({'Name': p, 'Z Order': entity_data[p]['Z Order']})
        z_order = sorted(z_order, key=lambda k: k['Z Order'])
        # Rendering each sprite
        for z in z_order:
            p = z['Name']
            data = entity_data[p]
            piece = entity.pieces[data['Piece']]
            wt = piece[2] - piece[0]
            ht = piece[3] - piece[1]
            piece_surface = entity.draw_piece(data['Piece'])
            piece_rect = pygame.Rect(tuple(data['Position']), (wt, ht))
            screen.blit(piece_surface, piece_rect)

    while player_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                player_running = False
        pygame.display.update()  # Or pygame.display.flip()
