from models import db, Genre, Character, Story, StoryStep
from flask_login import current_user
import openai   
import os

def create_prompt(selected_genres, selected_characters):

    genre_ids = [Genre.query.get(id) for id in selected_genres]
    genres = [genre.name for genre in genre_ids]
    character_ids = [(Character.query.get(id)) for id in selected_characters]
    characters = [(character.name, character.description) for character in character_ids]

    return ('a formatted choose your own adventure story, rated no higher than PG-13, using {} and {}.'.format(genres, characters))

def make_api_request(prompt):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a children's storyteller, creating a choose your own adventure story."},
            {"role": "system", "content": "Please return a succinct title labeled as [title], the body of the story labeled as [start_content], and exactly two short (ie. Go in Cave, or Go to Beach) choices each labeled exactly as [choice_text] with one choice each. All labels lower-case."},
            {"role": "system", "content": "After providing choices, stop the story. Do not provide summarization of choices."},
            {"role": "user", "content": prompt}
        ]
    )
    print(response)

    if response:
        response_content = response['choices'][0]['message']['content']
        response_parts = response_content.split('[choice_text]')

        title_start_content = response_parts[0].split('[start_content]')
        title = title_start_content[0].strip().replace('[title]\n', '')
        start_content = title_start_content[1].strip()

        choice1 = response_parts[1].strip()
        choice2 = response_parts[2].strip()
        print('1', choice1, '2', choice2)

        story = {
            "title": title,
            "start_content": start_content,
            "choice1": choice1,
            "choice2": choice2
        }

        new_story = Story.create_story(title=story['title'], start_content=story['start_content'], author_id=current_user.id)

        step1 = StoryStep(content=choice1, story_id=new_story.id)
        step2 = StoryStep(content=choice2, story_id=new_story.id)

        db.session.add(step1)
        db.session.add(step2)
        db.session.commit()

    return story