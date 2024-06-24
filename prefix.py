import random

prefixs = [
    "Make the style more minimal, giving the impression of a serene space.",
    "Use a bright color palette to evoke a sense of excitement and energy.",
    "Incorporate vintage elements to create a nostalgic feel.",
    "Design characters with exaggerated features for a cartoonish look.",
    "Create a dark, gothic atmosphere with intricate details.",
    "Implement a cyberpunk theme with neon lights and futuristic elements.",
    "Use pastel colors and soft lines for a dreamy, whimsical style.",
    "Add steampunk aesthetics with gears, pipes, and Victorian-era designs.",
    "Create a hand-drawn look with rough lines and sketchy details.",
    "Incorporate realistic textures and lighting for a lifelike appearance.",
    "Design with a pixel art style for a retro gaming feel.",
    "Use watercolor effects to give a fluid and artistic look.",
    "Create a monochromatic scheme to emphasize shapes and forms.",
    "Implement a space theme with stars, planets, and cosmic elements.",
    "Design characters and environments with a fantasy theme.",
    "Use low-poly models for a simplistic yet modern look.",
    "Incorporate nature elements like trees, rivers, and animals.",
    "Create a dystopian world with dark and decayed visuals.",
    "Use vibrant, contrasting colors for a bold and eye-catching style.",
    "Design with a medieval theme, including castles, knights, and dragons.",
    "Incorporate a comic book style with thick outlines and vibrant colors.",
    "Use geometric shapes to create abstract and modern visuals.",
    "Create a magical, enchanted forest with mystical creatures.",
    "Incorporate elements of street art and graffiti.",
    "Design a post-apocalyptic world with ruined buildings and scavengers.",
    "Use a cel-shaded technique for a comic book or anime-like appearance.",
    "Incorporate underwater themes with coral reefs and sea creatures.",
    "Create a whimsical, fairy tale world with magical elements.",
    "Use a noir style with high contrast and dramatic lighting.",
    "Design characters and environments inspired by ancient civilizations.",
    "Incorporate futuristic, robotic elements for a high-tech look.",
    "Use a bold, graphic style with sharp lines and strong contrasts.",
    "Create a cozy, homey atmosphere with warm colors and textures.",
    "Design with an industrial theme, including factories and machinery.",
    "Incorporate elements of surrealism for a dreamlike, fantastical feel.",
    "Use earthy tones and natural materials for an organic look.",
    "Design with a military theme, including soldiers and tanks.",
    "Incorporate elements of mythology and ancient legends.",
    "Create a whimsical, childlike style with playful characters.",
    "Use a high fantasy style with elves, wizards, and mythical creatures.",
    "Design with a sporty theme, including stadiums and athletes.",
    "Incorporate elements of horror with spooky, eerie visuals.",
    "Use a vibrant, tropical theme with bright colors and exotic plants.",
    "Create a medieval fantasy world with magic and epic quests.",
    "Design characters and environments with an anime-inspired style.",
    "Incorporate elements of urban culture and city life.",
    "Use a vintage sci-fi style with retro-futuristic designs.",
    "Create a mystical, ethereal world with glowing elements.",
    "Design with a wild west theme, including cowboys and deserts.",
    "Incorporate elements of traditional Asian art and culture.",
    "Use a sleek, modern style with clean lines and minimalistic design.",
    "Create a rugged, mountainous landscape with adventurers.",
    "Design characters and environments with a prehistoric theme.",
    "Incorporate elements of ancient Egyptian culture and mythology.",
    "Use a vibrant, carnival-like theme with bright lights and fun visuals.",
    "Create a peaceful, zen-like environment with calm colors.",
    "Design with a superhero theme, including capes and action poses.",
    "Incorporate elements of ancient Roman culture and architecture.",
    "Use a rustic, countryside theme with farms and rural landscapes.",
    "Create a high-speed, racing theme with fast cars and tracks.",
    "Design with a gothic horror theme, including haunted houses.",
    "Incorporate elements of ancient Greek mythology and legends.",
    "Use a cheerful, festive theme with bright decorations.",
    "Create a futuristic cityscape with towering skyscrapers.",
    "Design with a tropical island theme, including beaches and palm trees.",
    "Incorporate elements of Victorian fashion and architecture.",
    "Use a dark, moody color palette for a mysterious feel.",
    "Create a whimsical, carnival theme with funfair rides and games.",
    "Design with a historical theme, including famous landmarks.",
    "Incorporate elements of punk rock culture and fashion.",
    "Use a bold, adventurous style with daring characters.",
    "Create a serene, underwater world with marine life.",
    "Design with a high-tech, futuristic theme, including robots.",
    "Incorporate elements of medieval chivalry and honor.",
    "Use a colorful, abstract style with dynamic shapes.",
    "Create a serene, peaceful forest with gentle streams.",
    "Design with a space exploration theme, including astronauts.",
    "Incorporate elements of classical art and sculpture.",
    "Use a mystical, magical theme with enchanted forests.",
    "Create a rugged, desert landscape with nomadic tribes.",
    "Design with a cheerful, playful style for children.",
    "Incorporate elements of cyberpunk culture and neon lights.",
    "Use a natural, earthy palette for an organic feel.",
    "Create a whimsical, magical kingdom with fairy tale elements.",
    "Design with a pirate theme, including ships and treasure.",
    "Incorporate elements of ancient Norse mythology and Vikings.",
    "Use a bold, graphic novel style with intense visuals.",
    "Create a serene, mountain landscape with adventurers.",
    "Design with a futuristic sci-fi theme, including spaceships.",
    "Incorporate elements of ancient Japanese culture and samurai.",
    "Use a dynamic, action-packed style for high energy.",
    "Create a whimsical, enchanted garden with magical plants.",
    "Design with a high-fantasy theme, including dragons and castles.",
    "Incorporate elements of modern architecture and design.",
    "Use a vibrant, comic book style with dynamic characters.",
    "Create a peaceful, zen garden with calming elements.",
    "Design with a historical theme, including ancient ruins.",
    "Incorporate elements of horror with dark, eerie visuals.",
    "Use a cheerful, festive holiday theme with bright decorations.",
    "Create a serene, tranquil landscape with natural beauty.",
    "Design with a futuristic, high-tech theme, including robots.",
    "Incorporate elements of classical mythology and legends.",
]

def get_prefix():
    return random.choice(prefixs)