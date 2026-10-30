"""Small, distinct pixel paintings for meals, toys and room decorations."""
import pygame

TOYS = {'ball': ('STRIPED BALL', 0), 'yarn': ('YARN BALL', 45),
        'mouse': ('FELT MOUSE', 65), 'feather': ('FEATHER RATTLE', 80),
        'spring': ('RAINBOW SPRING', 100), 'butterfly': ('FLUTTER BUG', 125)}
INK = (58, 49, 73)


def food_frames(key):
    # Two frames keep the existing full/empty bowl animation contract.
    frames = []
    for full in (True, False):
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        rim = {'berries': (168, 116, 203), 'fish': (94, 166, 195), 'greens': (116, 177, 110),
               'feast': (228, 163, 86), 'milk': (130, 179, 213), 'soup': (222, 132, 108)}.get(key, (185, 129, 112))
        pygame.draw.ellipse(s, INK, (0, 6, 16, 9))
        pygame.draw.ellipse(s, rim, (1, 6, 14, 7))
        pygame.draw.line(s, (255, 239, 210), (3, 12), (11, 12))
        pygame.draw.ellipse(s, (85, 69, 81), (2, 6, 12, 5))
        if full:
            if key == 'milk':
                pygame.draw.ellipse(s, (255, 250, 230), (2, 5, 12, 5))
                pygame.draw.line(s, (196, 227, 239), (4, 8), (9, 8))
                s.set_at((5, 5), (255, 255, 255))
            elif key == 'soup':
                pygame.draw.ellipse(s, (244, 177, 67), (2, 5, 12, 5))
                for x, y in ((4, 6), (9, 7), (11, 5)):
                    pygame.draw.rect(s, (95, 155, 86), (x, y, 2, 2))
                pygame.draw.line(s, (237, 224, 197), (6, 3), (7, 1))
            elif key == 'fish':
                pygame.draw.ellipse(s, (250, 174, 158), (3, 3, 9, 6))
                pygame.draw.polygon(s, (220, 132, 136), ((10, 6), (14, 3), (14, 9)))
                pygame.draw.line(s, (255, 220, 192), (7, 4), (7, 7))
                s.set_at((5, 5), INK)
            elif key == 'greens':
                for x, y, c in ((3, 3, (79, 147, 78)), (7, 2, (133, 193, 91)), (10, 4, (68, 159, 112))):
                    pygame.draw.ellipse(s, c, (x, y, 5, 6))
                    pygame.draw.line(s, (212, 235, 145), (x+2, y+1), (x+2, y+4))
            elif key == 'berries':
                for x, y, c in ((3, 4, (197, 80, 118)), (7, 2, (111, 103, 186)), (10, 5, (205, 82, 139)), (6, 6, (96, 113, 185))):
                    pygame.draw.circle(s, c, (x+1, y+1), 2)
                    s.set_at((x, y), (249, 204, 228))
                pygame.draw.line(s, (96, 161, 90), (7, 2), (10, 1))
            elif key == 'feast':
                pygame.draw.rect(s, (250, 232, 185), (3, 3, 4, 6))
                pygame.draw.rect(s, (236, 141, 106), (8, 4, 4, 3))
                pygame.draw.rect(s, (106, 176, 107), (9, 7, 4, 2))
                s.set_at((4, 5), (195, 165, 118)); s.set_at((5, 7), (195, 165, 118))
            else:
                for x, y in ((3, 5), (7, 4), (11, 5), (5, 7), (9, 7)):
                    pygame.draw.rect(s, (190, 126, 75), (x, y, 3, 2))
                    s.set_at((x, y), (241, 184, 105))
        frames.append(s)
    return frames


def toy_image(key):
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    if key == 'spring':
        for i, color in enumerate(((238, 142, 172), (249, 202, 105), (120, 198, 166), (159, 151, 218))):
            pygame.draw.ellipse(s, INK, (2, 2+i*3, 12, 5), 1)
            pygame.draw.ellipse(s, color, (3, 2+i*3, 10, 4), 1)
    elif key == 'butterfly':
        for x in (1, 8):
            pygame.draw.ellipse(s, (182, 137, 217), (x, 2, 7, 9))
            pygame.draw.ellipse(s, (244, 175, 197), (x+1, 7, 6, 7))
            pygame.draw.circle(s, (255, 220, 128), (x+3, 5), 2)
        pygame.draw.line(s, INK, (8, 3), (8, 13), 2)
    elif key == 'mouse':
        pygame.draw.line(s, (220, 151, 174), (3, 11), (1, 12))
        pygame.draw.line(s, (220, 151, 174), (1, 12), (1, 8))
        pygame.draw.ellipse(s, INK, (3, 5, 12, 9))
        pygame.draw.ellipse(s, (174, 177, 201), (4, 6, 10, 7))
        pygame.draw.circle(s, (234, 172, 186), (8, 6), 3)
        s.set_at((12, 9), INK); s.set_at((14, 11), (236, 141, 155))
    elif key == 'feather':
        pygame.draw.line(s, (176, 121, 76), (4, 14), (11, 3), 2)
        pygame.draw.ellipse(s, INK, (6, 0, 9, 9))
        pygame.draw.ellipse(s, (71, 181, 168), (7, 1, 7, 7))
        pygame.draw.line(s, (175, 230, 180), (8, 7), (12, 2))
        pygame.draw.circle(s, (240, 199, 92), (5, 12), 2)
    else:
        pygame.draw.circle(s, INK, (8, 8), 7)
        pygame.draw.circle(s, (190, 118, 187) if key == 'yarn' else (237, 162, 100), (8, 8), 6)
        if key == 'yarn':
            for y in (5, 8, 11): pygame.draw.line(s, (240, 192, 221), (4, y), (12, y-2))
            pygame.draw.line(s, (129, 83, 149), (6, 3), (10, 13), 1)
        else:
            pygame.draw.rect(s, (113, 184, 183), (3, 7, 10, 3))
            pygame.draw.line(s, (255, 231, 173), (7, 3), (7, 13), 2)
        pygame.draw.rect(s, (255, 237, 218), (4, 4, 2, 2))
    return s


def decor_image(key):
    s = pygame.Surface((32, 32), pygame.SRCALPHA)
    if key == 'flowers':
        pygame.draw.polygon(s, INK, ((8, 21), (24, 21), (21, 31), (11, 31)))
        pygame.draw.polygon(s, (158, 184, 203), ((10, 22), (22, 22), (20, 29), (12, 29)))
        for x, y, col in ((10, 10, (239, 153, 181)), (20, 12, (186, 158, 225)), (16, 5, (252, 209, 112))):
            pygame.draw.line(s, (89, 143, 95), (x, y), (16, 23), 2)
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                pygame.draw.circle(s, col, (x+dx, y+dy), 3)
            pygame.draw.circle(s, (255, 243, 195), (x, y), 2)
    elif key == 'lamp':
        pygame.draw.line(s, INK, (16, 14), (16, 29), 3)
        pygame.draw.ellipse(s, INK, (8, 27, 16, 4))
        pygame.draw.ellipse(s, (188, 154, 110), (10, 27, 12, 2))
        pygame.draw.polygon(s, INK, ((9, 2), (23, 2), (29, 16), (3, 16)))
        pygame.draw.polygon(s, (252, 218, 145), ((10, 3), (22, 3), (26, 14), (6, 14)))
        pygame.draw.line(s, (255, 240, 186), (12, 5), (10, 12), 2)
    elif key == 'books':
        pygame.draw.rect(s, INK, (2, 4, 28, 28))
        pygame.draw.rect(s, (161, 111, 86), (4, 6, 24, 24))
        for y in (8, 20):
            for x, col in ((6, (113, 174, 166)), (11, (219, 144, 151)), (17, (232, 194, 111)), (23, (150, 140, 198))):
                pygame.draw.rect(s, col, (x, y, 3, 8))
                s.set_at((x+1, y+2), (255, 237, 199))
        pygame.draw.rect(s, (211, 157, 107), (4, 17, 24, 3))
    return s
