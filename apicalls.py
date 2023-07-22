from models import db, Genre, Character, Story, StoryStep, Choice, StoryCharacters
from flask_login import current_user
import openai   
import os

openai.api_key = os.getenv('OPENAI_API_KEY')

def make_api_request(selected_genres, selected_characters):

    genre_ids = [Genre.query.get(id) for id in selected_genres]
    genres = [genre.name for genre in genre_ids]
    character_ids = [(Character.query.get(id)) for id in selected_characters]
    characters = [(character.name, character.description) for character in character_ids]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a storyteller, creating a formatted choose your own adventure story, rated no higher than PG-13, with the genres of {} and the characters of {}.".format(genres, characters)},
            {"role": "system", "content": "Use these exact tags to separate story parts. [title]generate a short title, [start_content] generate a 400-500 word story, [choice_text] generate first short choice, [choice_text] generate second short choice"},
            {"role": "system", "content": "After providing choices, stop the story; do not simulate making a choice. Do not return anything not explicitly requested. All labels lower-case."}
        ]
    )

    print(response)

    if response:
        response_content = response['choices'][0]['message']['content']
        response_parts = response_content.split('[choice_text]')

        title_start_content = response_parts[0].split('[start_content]')
        title = title_start_content[0].strip().replace('[title]', '').strip()
        start_content = title_start_content[1].strip()

        choice1 = response_parts[1].strip()
        choice2 = response_parts[2].strip()

        new_story = Story.create_story(title=title, start_content=start_content, author_id=current_user.id)

        step1 = StoryStep(content=choice1, story_id=new_story.id)
        step2 = StoryStep(content=choice2, story_id=new_story.id)

        db.session.add(step1)
        db.session.add(step2)
        db.session.commit()

        for id in selected_characters:
            new_storycharacters = StoryCharacters(story_id=new_story.id, character_id=id)

            db.session.add(new_storycharacters)
            db.session.commit()

    return new_story

def next_step(id, new_choice):

    story = Story.query.get_or_404(id)
    choice = Choice.query.get_or_404(new_choice.id)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a storyteller, continuing a formatted choose your own adventure story, rated no higher than PG-13. The story should be long and engaging, not ending after a single branch."},
            {"role": "user", "content": story.start_content + " " + choice.choice_text},
            {"role": "system", "content": "Use these exact tags to separate story parts. [start_content] generate a 400-500 word story, [choice_text] generate first short choice, [choice_text] generate second short choice. Only if the story ends, use [end_content]."},
            {"role": "system", "content": "After providing new choices, stop the story; do not simulate making a choice. Do not repeat anything from prompt. Do not return anything not explicitly requested. All labels lower-case."}
        ]
    )

    print(response)
    if response:
        response_content = response['choices'][0]['message']['content'].replace('[start_content]', '').strip()

        if '[end_content]' in response_content:
            end_content = response_content.replace('[end_content]', '').strip()
            new_story = Story.create_story(title=story.title, start_content=end_content, author_id=current_user.id, end=True)
        
        else:
            response_parts = response_content.split('[choice_text]')

            start_content = response_parts[0].strip()

            choice1 = response_parts[1].strip()
            choice2 = response_parts[2].strip()

            new_story = Story.create_story(title=story.title, start_content=start_content, author_id=current_user.id)

            step1 = StoryStep(content=choice1, story_id=new_story.id)
            step2 = StoryStep(content=choice2, story_id=new_story.id)

            db.session.add(step1)
            db.session.add(step2)
            db.session.commit()

    return new_story

