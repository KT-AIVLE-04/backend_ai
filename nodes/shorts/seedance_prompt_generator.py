from config.settings import settings
from states.shorts_state import ShortsState
import os
import re
import json
import base64
import random
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import anthropic


def seedance_prompt_generation(state: ShortsState) -> ShortsState:
    client = anthropic.Anthropic(api_key = settings.claude_api_key)
    
    scene_descriptions = [scene.content for scene in state.scenes]
    
    if len(scene_descriptions) != len(state.scenes_image_list):
      raise ValueError(f"씬 수({len(scene_descriptions)})와 이미지 수({len(state.scenes_image_list)})가 일치하지 않음")

    
    print("Seedance 프롬프트 생성 시작")
    print("=" * 60)

    business_info = {
        "store_name": state.store_name,
        "business_type": state.business_type,
        "brand_concept": state.brand_concept,
        "target_audience": state.target_audience,
        "platform": state.platform,
        "ad_type": state.ad_type
    }
    
    state.seedance_results = []
    previous_prompt = ""
    is_ending = False

    try:
        for i in range(len(scene_descriptions)):
            print(f"\nScene {i+1}/{len(scene_descriptions)} 처리 중...")

            # 현재 씬 & 다음 씬 정보
            current_scene = scene_descriptions[i]
            start_frame = state.scenes_image_list[i]

            # 다음 씬 정보
            if i < len(scene_descriptions) - 1:
                is_ending = False

                tail_frame = state.scenes_image_list[i + 1]
                next_scene = scene_descriptions[i + 1]
            
                print(f"현재 씬: '{current_scene[:30]}...'")
                print(f"다음 씬: '{next_scene[:30]}...'")

            else:
                # 마지막 씬 (None)
                is_ending = True

                tail_frame = None
                next_scene = None
                
                print(f"마지막 씬: '{current_scene[:30]}...'")


            # 최초 Seedance 프롬프트 생성
            result = generate_seedance_prompt(
                client = client,
                start_image_path = start_frame,
                tail_image_path = tail_frame,
                scene_description = current_scene,
                next_scene_description = next_scene,
                scene_index = i,
                total_scenes = len(scene_descriptions),
                business_info = business_info,
                previous_prompt = previous_prompt,
                is_ending = is_ending,
                all_scenes = scene_descriptions
            )

            prompt = result["prompt"]

            # 최적화
            prompt = optimize_prompt_for_seedance(client, prompt)

            
            # 대체 버전 생성 (옵션)
            alternatives = []
            alternatives = generate_alternative_versions(client, prompt, 1)
            
            # 결과 저장
            final_result = {
                "scene_index": i,
                "scene_description": current_scene,
                "next_scene_description": next_scene,
                "start_frame": start_frame,
                "tail_frame": tail_frame,
                "main_prompt": prompt,
                "alternative_prompts": alternatives,
                "metadata": result["metadata"],
                "character_analysis": result.get("character_analysis"),
                "transition_to_next": next_scene is not None,
                "timestamp": datetime.now().isoformat()
            }

            state.seedance_results.append(final_result)
            previous_prompt = prompt

            
            print(f"완료: {len(prompt.split())} words")
            
            if next_scene:
                print(f"다음 씬으로 연결 준비")


        # validation
        print("\n시퀀스 연속성 검증...")
        state.seedance_validation = validate_sequence(state.seedance_results)

        print("\n" + "=" * 60)
        print(f"Seedance 프롬프트 생성 완료")
        print(f"총 {len(state.seedance_results)}개 씬 처리")
        print(f"씬 연결: {sum(1 for r in state.seedance_results if r['transition_to_next'])}개")
        print(f"평균 프롬프트 길이: {state.seedance_validation['avg_length']} words")
        print(f"형식 검증: {state.seedance_validation['format_check']}")

        return state
      
    except Exception as e:
       raise Exception(f"Seedance 프롬프트 생성 실패: {str(e)}")




# ================= Helper Functions =================

def generate_seedance_prompt(client: anthropic.Anthropic,
                             start_image_path: Optional[str] = None,
                             tail_image_path: Optional[str] = None,
                             scene_description: Optional[str] = None,
                             next_scene_description: Optional[str] = None,
                             scene_index: int = 0,
                             total_scenes: int = 1,
                             business_info: Optional[Dict[str, Any]] = None,
                             previous_prompt: Optional[str] = None,
                             is_ending: bool = False,
                             all_scenes: Optional[List[str]] = None) -> Dict[str, Any]:
        
    """Seedance 텍스트 프롬프트 생성"""    
    if not is_ending and tail_image_path:
        character_analysis = analyze_character_difference(client, start_image_path, tail_image_path)

        transition_strategy = determine_transition_strategy(character_analysis)


    else:
        character_analysis = {"description": "Final scene - No transition needed"}
        transition_strategy = {
          "system_rules": """
          ENDING SCENE RULES:
          - Create a powerful, conclusive ending
          - Emphasize brand identity and message
          - End with a memorable final shot
          - No transition needed after this scene
          """,
          "user_instruction": "Create a strong ending that concludes the narrative",
          "ending_instruction": "Ends with a powerful, memorable final moment"
        }

    # 비즈니스 정보 분석 (스타일 가이드 생성)
    style_guide = analyze_business_context(client, business_info) if business_info else ""

     # 이전 프롬프트 분석
    continuity_hint = analyze_previous_prompt(previous_prompt) if previous_prompt else ""

    if is_ending:
        narrative_summary = ""
      
        if all_scenes:
            narrative_summary = f"""
            NARRATIVE CONTEXT (for ENDING):
            Full story arc: {' → '.join([s[:50] + '...' for s in all_scenes])}
        
            Create an ending that:
            - Resolves the narrative
            - Reinforces the brand message
            - Leaves a lasting impression
            """

    # 엔딩 씬 시스템 프롬프트
    if is_ending:
        system_prompt = f"""
        You are an expert Seedance-1 prompt engineer. Generate ONLY text prompts in the exact format Seedance requires.

        CRITICAL RULES:
        1. Output format: Plain text starting with "Multiple shots."
        2. Use [Shot type] tags precisely: [Wide shot], [Close-up], [Tracking shot], etc.
        3. Use transition tags between shots: [Cut to], [Dissolve to], [Pan to], etc.
        4. End with a complete, powerful moment (with period)
        5. Keep total prompts length under 100-120 words
        6. Focus on cinematic, dynamic descriptions
        7. Include specific visual details, movements, and atmosphere
        8. Be specific about character appearances

        {transition_strategy['system_rules']}

        NEVER output JSON. Only output the plain text prompt.
        """
    
    # 처음 씬 + 중간 씬 시스템 프롬프트
    else:  
        system_prompt = f"""
        You are an expert Seedance-1 prompt engineer. Generate ONLY text prompts in the exact format Seedance requires.

        CRITICAL RULES:
        1. Output format: Plain text starting with "Multiple shots."
        2. Use [Shot type] tags precisely: [Wide shot], [Close-up], [Tracking shot], etc.
        3. Use transition tags between shots: [Cut to], [Dissolve to], [Pan to], etc.
        4. End with an incomplete action verb or mid-motion description WITHOUT punctuation (no period at end)
            - Good: "as the figure turns to", "while the camera pushes through", "begins to reach for"
            - Bad: "as the figure begins to..." (too vague)
        5. Keep total prompts length under 100-120 words
        6. Focus on cinematic, dynamic descriptions
        7. Include specific visual details, movements, and atmosphere
        8. Be specific about character appearances

        {transition_strategy['system_rules']}
        
        ENDING RULES:
        - End with incomplete action: "as the figure turns toward"
        - NO period at the very end
        - NO "..." at the end
        - Leave action unfinished for natural flow

        NEVER output JSON. Only output the plain text prompt.
        """

    # 엔딩 씬 유저 프롬프트
    if is_ending:
        user_prompt = f"""
        FINAL SCENE {scene_index + 1}/{total_scenes}: "{scene_description}"
        
        {style_guide}

        {continuity_hint}

        {narrative_summary if all_scenes else ''}
        
        This is the ENDING scene. Create a powerful conclusion that:
        1. Starts from the START frame
        2. Builds to a memorable climax
        3. Ends with impact and closure
        
        Brand/Business Context: 
        - Store: {business_info.get('store_name')}
        - Type: {business_info.get('business_type')}
        - Brand Concept: {', '.join(business_info.get('brand_concept', []))}
        - Target: {business_info.get('target_audience')}
        
        End with a complete, impactful final shot.
        """

     # 처음 씬 + 중간 씬 유저 프롬프트
    else:
        next_scene_info = ""
        
        if next_scene_description:
            next_scene_info = f"""
            IMPORTANT: The TAIL FRAME is the beginning of the NEXT scene:
            Next Scene Description: "{next_scene_description}"

            Your ending should naturally lead into this next scene by:
            """

        user_prompt = f"""
        Create a Seedance prompt for:
        - CURRENT Scene {scene_index + 1} of {total_scenes}
        - CURRENT Description: "{scene_description}"
        
        {next_scene_info}
        
        {style_guide}
        
        {continuity_hint}

        CHARACTER ANALYSIS:
        {character_analysis['description']}
        
        TRANSITION REQUIREMENT:
        {transition_strategy['user_instruction']}


        You have TWO images:
        1. START FRAME: Where THIS scene begins (current scene start)
        2. TAIL FRAME: Where THIS scene must end (this is the start of the NEXT scene)

        Analyze both images and create a prompt that:
        1. Starts with the CURRENT scene's beginning (START frame)
        2. Develops the CURRENT scene's narrative
        3. {transition_strategy['ending_instruction']}

        
        The prompt should:
        - Begin with the START frame composition showing {scene_description}
        - Progress naturally through 2-3 shots developing the current scene
        - End approaching the TAIL frame composition that sets up the next scene
        - Include atmospheric details
        - End with a SPECIFIC ACTION in progress (not just "...")

        ENDING EXAMPLES:
        - "as the camera pushes through the mist revealing"
        - "while her hand reaches toward the glowing"
        - "the subject turns to face the approaching"
        - "sparks fly as the metal strikes"


        Examples of Good Seedance prompts:
        - "Multiple shots. A boy with curly hair and a backpack rides a bike down a golden-lit rural road at sunset. [Cut to] He slows down and looks toward a field of tall grass. [Wide shot] His silhouette halts in the orange haze as dust particles dance around."
        - "Multiple shots. [Wide aerial shot] In the heart of a ruined city, squads of futuristic soldiers exchange laser fire across broken streets, muzzle flashes reflecting off shattered windows under a sky choked with smoke. [Tracking shot] The camera glides through collapsing debris as explosions."

        Now generate ONLY the text prompt. No JSON, no explanations, just the prompt text.
        """

    
    # 엔딩 씬 messages
    if is_ending:
        messages_content = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "START FRAME of the ENDING scene:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": start_image_path
                        }
                    },
                    {
                        "type": "text",
                        "text": "\n" + user_prompt
                    }
                ]
            }
        ]
    
    
    # 처음 씬 & 중간 씬 messages
    else:
        messages_content = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "START FRAME (beginning):"
                    },
                    {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": start_image_path
                            }
                        },
                        {
                            "type": "text",
                            "text": "\nTAIL FRAME (ending goal):"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": tail_image_path
                            }
                        },
                        {
                            "type": "text",
                            "text": "\n" + user_prompt
                        }
                ]
            }
        ]
    
    
    try:
        response = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens = 500,
            temperature = 0.2,
            system = system_prompt,
            messages = messages_content
        )

        
        seedance_prompt = response.content[0].text.strip()

        # 프롬프트 검증 및 최적화
        if is_ending:
            if not seedance_prompt.startswith("Multiple shots"):
                seedance_prompt = "Multiple shots. " + seedance_prompt
        
        else:
            seedance_prompt = validate_prompt(seedance_prompt)

        
        if not is_ending and character_analysis.get('different_person'):
            seedance_prompt = enhance_transition_for_character_change(seedance_prompt, transition_strategy)

        
        # 메타데이터 생성
        metadata = generate_prompt_metadata(seedance_prompt, scene_index)
        metadata['character_transition'] = character_analysis
        metadata['is_ending'] = is_ending

        
        return {
            "prompt": seedance_prompt,
            "metadata": metadata,
            "character_analysis": character_analysis
        }

    
    except Exception as e:
      raise Exception(f"Seedance 프롬프트 생성 실패: {str(e)}")



def analyze_business_context(client: anthropic.Anthropic,
                             business_info: Dict[str, Any]) -> str:
    """비즈니스 정보 분석 및 스타일 가이드라인 생성"""
    
    if not business_info:
        return ""

    system_prompt = """
    You are a visual storytelling expert who translates brand identity into cinematic language for Seedance video generation.

    Your task: Convert business information into SPECIFIC visual directives that enhance video quality.

    Focus on:
    1. VISUAL MOOD - Translate brand values into lighting/color mood
    2. CAMERA LANGUAGE - Match brand personality with camera movement style
    3. PACING - Determine rhythm based on target audience
    4. PRODUCTION VALUE - Set quality level based on brand positioning
    5. SIGNATURE ELEMENTS - Identify unique visual markers

    Output format: A concise, actionable visual style guide in 2-3 sentences.

    Be SPECIFIC with cinematography terms, not generic marketing language.
    """

    
    user_prompt = f"""
    Business Information:
    - Store: {business_info.get('store_name')}
    - Type: {business_info.get('business_type')}
    - Brand Concept: {', '.join(business_info.get('brand_concept', []))}
    - Ad Type: {business_info.get('ad_type')}
    - Target: {business_info.get('target_audience')}

    Analyze and create a CINEMATIC style guide that includes:

    VISUAL TONE:
    - If luxury/premium → "High contrast, dramatic lighting, slow deliberate movements"
    - If tech/innovative → "Clean compositions, cool color grading, dynamic transitions"
    - If natural/organic → "Soft natural light, handheld authenticity, earthy tones"
    - If energetic/youth → "Vibrant colors, rapid cuts, kinetic camera work"

    CAMERA STYLE:
    - Corporate → "Smooth steadicam, controlled movements"
    - Creative → "Dynamic handheld, unexpected angles"
    - Luxury → "Slow cinematic dollies, elegant crane shots"
    - Tech → "Precise geometric movements, clean transitions"

    PACING:
    - Gen Z audience → "Quick cuts, high energy, 2-3 second shots"
    - Millennials → "Moderate pacing, 3-4 second shots"
    - Professional → "Deliberate pacing, 4-5 second shots"
    - Luxury market → "Slow, contemplative, 5-6 second shots"

    MOOD ELEMENTS:
    - Brand personality → Specific atmospheric elements
    - Industry conventions → Expected visual language
    - Competitive differentiation → Unique visual signatures

    Create a style guide that a cinematographer would actually use.
    Example output: "Employ slow, deliberate camera movements with high contrast lighting and deep shadows. Maintain elegant composition with subtle handheld energy for authenticity. Color grade toward desaturated blues with warm skin tones."

    Now create the style guide:
    """

    try:
        response = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens = 200,
            temperature = 0.4,
            system = system_prompt,
            messages = [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        return f"\nVISUAL STYLE DIRECTIVE: {response.content[0].text.strip()}\n"

    except Exception as e:
        print(f"스타일 가이드 생성 실패: {str(e)}")
        
        return ""



def analyze_character_difference(client: anthropic.Anthropic,
                                 start_path: str,
                                 tail_path: str) -> Dict[str, Any]:

    """이미지 내 등장인물 분석"""
          
          
    analysis_prompt = """
    Compare the main human characters in these two images.
    
    Analyze:
    1. Gender of main character(s) in each image
    2. Are they the same person or different people?
    3. Key visual differences (if different people)
    
    Respond in this excat JSON format:
    {
      "has_characters": True/False,
      "start_character": "brief description (e.g., 'young woman with long hair') or 'no person'",
      "tail_character": "brief description (e.g., 'young woman with long hair') or 'no person'",
      "same_person": True/False,
      "gender_change": True/False,
      "key_differences": ["list of main differences if different people"]
    }
    """
    
    try:
        response = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens = 300,
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Image 1 (START):"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": start_path,
                            }
                        },
                        {
                            "type": "text",
                            "text": "\nImage 2 (TAIL):"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": tail_path
                            }
                        },
                        {
                            "type": "text", 
                            "text": "\n" + analysis_prompt
                        }
                    ]
                }
            ]
        )
    
        # JSON Parsing
        response_text = response.content[0].text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            analysis = json.loads(json_match.group())
            analysis['different_person'] = not analysis.get('same_person', True)
            analysis['description'] = format_character_analysis(analysis)

            return analysis
        

        # return {
        #     "start_character": analysis.get("start_character", "person in scene"),
        #     "tail_character": analysis.get("tail_character", "person in scene"),
        #     "same_person": analysis.get("same_person", True),
        #     "different_person": not analysis.get("same_person", True),
        #     "gender_change": analysis.get("gender_change", False),
        #     "key_differences": analysis.get("key_differences", []),
        #     "description": format_character_analysis(analysis)
        # }
    
    
    except Exception as e:
        print(f"인물 분석 실패: {str(e)}")

  
    # 분석 실패 시 None 데이터 대체
    return {
        "has_characters": None,
        "same_person": True,
        "different_person": False,
        "description": "Character analysis not available"
    }
    


def determine_transition_strategy(character_analysis: Dict[str, Any]) -> Dict[str, str]:
    """인물 변화에 따른 전환 전략 설정"""

      
    # 인물이 없는 경우
    if character_analysis.get('has_characters') == False:
        return {
            "system_rules": """
            SCENE TRANSITION RULES (No Characters):
            - Focus on environmental and visual continuity
            - Use camera movements to connect scenes
            - Emphasize objects, atmosphere, or spatial transitions
            """,
            "user_instruction": "No characters detected. Focus on environmental/object continuity.",
            "ending_instruction": "Smoothly transitions through environment/objects to TAIL frame",
            "examples": """
            EXAMPLES for scenes without characters:
            - "...camera glides through the empty space toward"
            - "...light shifts across the surface as"
            - "...focus pulls from foreground object to"
            """
        }

    # 인물이 있지만, 같은 인물인 경우
    if not character_analysis.get('different_person', False):
        # 같은 인물
        return {
            "system_rules": """
            CHARACTER CONSISTENCY RULES:
            - Maintain the same character throughout the scene
            - Use standard cuts and transitions
            - Never use vague terms like "person" or "figure" if gender is known
            - Repeat key characteristics in each shot for consistency
            """,
            "user_instruction": "Maintain character continuity throughout the scene.",
            "ending_instruction": "Naturally transitions toward the TAIL frame",
            "examples": ""
        }

    elif character_analysis['gender_change']:
        # 성별 다른 인물
        return {
            "system_rules": """
            CHARACTER TRANSITION RULES (Different Person):
            - The START and TAIL frames show DIFFERENT people
            - Use creative transitions to bridge between different characters
            - PREFERRED TRANSITIONS for character changes:
              * [Fade to] - for complete character replacement
              * [Dissolve to] - for smooth character transition
              * [Match cut to] - when matching similar poses/actions
            - Use environmental elements (objects, shadows, crowds) to mask the transition
            - Avoid direct cuts between different people's faces
            - Never use vague terms like "person" or "figure" if gender is known
            """,
            "user_instruction": f"""
            DIFFERENT CHARACTERS DETECTED:
            - Start: {character_analysis['start_character']}
            - End: {character_analysis['tail_character']}
            
            You MUST use smooth transitions (Fade/Dissolve/Match cut) to bridge between these different people.
            """,
            "ending_instruction": "Uses a SMOOTH TRANSITION (fade/dissolve/environmental bridge) to the different person in TAIL frame",
            "examples": """
            GOOD TRANSITION EXAMPLES for different people:
            - "...[Fade to] A different figure emerges from the shadows as"
            - "...[Dissolve to] Through the crowd, another person appears walking"
            - "...camera pans across the room. [Match cut to] Similar pose but different person turning"
            - "...focuses on an object. [Dissolve to] Different hands reaching for the same object"
            """
        }

    else:
        # 같은 성별의 다른 인물 전환 (또는 유사 인물)
        return {
            "system_rules": """
            CHARACTER TRANSITION RULES (Similar/Different Person):
            - The frames may show different people with similar appearance
            - Use smooth transitions when changing between characters
            - Consider using [Match cut to] for similar poses
            - Use [Dissolve to] for gradual character changes
            - Never use vague terms like "person" or "figure" if gender is known
            """,
            "user_instruction": f"""
            Character transition detected:
            - Start: {character_analysis['start_character']}
            - End: {character_analysis['tail_character']}
            
            Use appropriate transitions if characters are different.
            """,
            "ending_instruction": "Smoothly transitions to the character in TAIL frame",
            "examples": """
            TRANSITION EXAMPLES:
            - "...[Match cut to] Similar figure in the same position"
            - "...[Dissolve to] The scene shifts to reveal"
            """
        }



def format_character_analysis(analysis: Dict[str, Any]) -> str:
    """인물 분석 결과 포맷팅"""
      
    # 인물이 없는 경우
    if analysis.get("has_characters") == False:
        return f"No characters in scene. Main focus: {analysis.get('main_subject', 'environment/objects')}"
    
    # 인물이 있는 경우
    if analysis.get("same_person", True):
        return f"Same character throughout: {analysis.get('start_character', 'person')}"
    
    else:
        desc = f"Different characters detected:\n"
        desc += f"- START: {analysis.get('start_character', 'person')}\n"
        desc += f"- TAIL: {analysis.get('tail_character', 'person')}"
        if analysis.get("key_differences"):
            desc += f"\n- Key differences: {', '.join(analysis['key_differences'][:3])}"
        
        return desc



def enhance_transition_for_character_change(prompt: str,
                                            transition_strategy: Dict[str, str]) -> str:
    """인물 변화가 있을 때 전환 강화"""
    
    # 기본 Cut to를 더 부드러운 전환으로 교체
    if '[Cut to]' in prompt:
        # 마지막 Cut to를 Fade 또는 Dissolve 또는 Match cut으로 변경
        replacements = ['[Fade to]', '[Dissolve to]', '[Match cut to]']
            
        chosen = random.choice(replacements)
            
        # 마지막 [Cut to]만 교체
        parts = prompt.rsplit('[Cut to]', 1)
        
        if len(parts) == 2:
            prompt = parts[0] + chosen + parts[1]
    
    return prompt



def generate_alternative_versions(client: anthropic.Anthropic,
                                  base_prompt: str,
                                  variation_count: int = 1) -> List[str]:
    """기본 프롬프트 대체 버전 생성"""

    system_prompt = """
    You are a Seedance prompt variation expert.

    Given a base prompt, create variations with:
    - Different camera angles
    - Different pacing (fast/slow)
    - Different transition styles
    - Same start and end points

    Output ONLY the prompt text, one per line.
    """

    user_prompt = f"""
    Base prompt: "{base_prompt}"

    Create {variation_count} variations of this prompt.
    Each should maintain the same narrative but with different:
    1. Camera work (angles, movements)
    2. Pacing (shot duration, transition speed)
    3. Emphasis (what to focus on)

    Output each variation on a new line, no numbering, no explanations.
    """

    try:
        response = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens = 500,
            temperature = 0.8,
            system = system_prompt,
            messages = [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        # 각 라인을 개별 프롬프트로 분리
        variations = [
            line.strip()
            for line in response.content[0].text.strip().split('\n')
            if line.strip() and line.strip().startswith("Multiple shots")
        ]

        return variations[:variation_count]

    except Exception as e:
        print(f"대체 프롬프트 생성 실패: {str(e)}")

        return [base_prompt]



def optimize_prompt_for_seedance(client: anthropic.Anthropic, prompt: str) -> str:
    """Seedance 프롬프트 최적화"""

    system_prompt = """
    You are a master cinematographer and Seedance-1 optimization specialist who understands exactly what makes Seedance generate stunning videos.

    SEEDANCE STRENGTHS TO LEVERAGE:
    • Excels at: Dynamic camera movements, lighting transitions, particle effects, realistic motion blur
    • Best with: Specific action verbs, precise spatial descriptions, cinematic terminology
    • Handles well: Rain/water effects, smoke/fog, fabric movement, reflections, depth of field changes

    OPTIMIZATION RULES:
    1. Replace generic descriptions with SPECIFIC cinematic language
    2. Add LAYERED visual elements (foreground/midground/background)
    3. Include MOTIVATED camera movements (not random)
    4. Enhance with ATMOSPHERIC effects that add production value
    5. Use PRECISE directional terms (camera left, foreground right, etc.)
    6. Add TEXTURE details (rough, glossy, matte, translucent)
    7. Include LIGHT INTERACTION (rim lighting, backlight, reflections)
    8. Specify MOTION DYNAMICS (accelerating, decelerating, oscillating)

    FORBIDDEN:
    - Don't add new plot elements
    - Don't change the core narrative
    - Don't exceed 120 words
    - Don't use abstract or vague terms
    - Don't add text/UI elements
    - Keep character descriptions consistent

    Output ONLY the optimized prompt. Start with "Multiple shots."
    """

    user_prompt = f"""
    Original prompt: "{prompt}"

    ENHANCEMENT CHECKLIST:
    CAMERA WORK - Make more cinematic:
    - Static → Slow push/pull/drift
    - Pan → Sweeping arc/Whip pan/Parallax pan
    - Simple tracking → Orbital track/Steadicam follow/Crane movement
    - Add: Rack focus moments, depth changes, handheld energy where appropriate

    LIGHTING - Add cinematic quality:
    - Natural light → Golden hour/Blue hour/Overcast diffusion
    - Indoor → Practical lights/Neon spill/Window shafts
    - Add: Lens flares, light leaks, volumetric rays, color temperature shifts

    ATMOSPHERE - Layer environmental effects:
    - Clear air → Atmospheric haze/Fog layers/Dust motes
    - Static background → Moving elements/Wind effects/Particle systems
    - Add: Weather appropriate to mood (mist, rain, snow particles)

    MOTION - Enhance dynamics:
    - Simple movement → Complex trajectories with acceleration
    - Static elements → Secondary motion (hair, fabric, debris)
    - Add: Motion blur, speed ramping hints, kinetic energy

    DETAILS - Add production value:
    - Surfaces → Specific textures (wet asphalt, brushed metal, frosted glass)
    - Colors → Precise color grading terms (teal-orange, desaturated blues)
    - Materials → How they catch light (iridescent, matte, glossy)

    ENDING - Make more dynamic:
    - If ending is weak → Add specific incomplete action
    - Ensure it ends mid-motion with clear momentum
    - Final frame should have kinetic energy

    EXAMPLES OF IMPROVEMENTS:

    Bad: "Person walks down street"
    Good: "Figure strides through rain-slicked streets, neon reflections rippling"

    Bad: "Camera moves around subject"
    Good: "Camera orbits clockwise, parallax revealing layered depth"

    Now optimize the prompt using these techniques.

    MAINTAIN:
    - Original narrative structure
    - Character continuity
    - Scene relationships
    
    Remember: End mid-action without punctuation.

    Output only the improved prompt, no explanations.
    """

    try:
        response = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens = 500,
            temperature = 0.4,
            system = system_prompt,
            messages = [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        return response.content[0].text.strip()

    except Exception as e:
        print(f"최적화 실패: {str(e)}")
        return prompt



def analyze_previous_prompt(previous_prompt: str) -> str:
    """이전 프롬프트 분석 (연속성 확보)"""
    if not previous_prompt:
        return ""
    
    last_words = previous_prompt.split()[-10:] if previous_prompt else []
    
    return f"Previous ending: {' '.join(last_words)}"



def validate_prompt(prompt: str) -> str:
    """프롬프트 검증 및 최적화"""
    
    # Multiple shots로 시작하는지 확인
    if not prompt.startswith("Multiple shots"):
        prompt = "Multiple shots. " + prompt
    
    prompt = prompt.rstrip('.')
    
    # ... 제거
    if prompt.endswith('...'):
        prompt = prompt[:-3]
    
    return prompt



def generate_prompt_metadata(prompt: str, scene_index: int) -> Dict[str, Any]:
    """메타데이터 생성"""
    # 샷 카운트
    shot_count = prompt.count('[')

    # 전환 타입 추출
    transitions = []
    for transition in ["Cut to", "Dissolve to", "Pan to", "Track to", "Fade to"]:
        if f"[{transition}]" in prompt:
            transitions.append(transition)

    # 카메라 무브먼트 추출
    movements = []
    for movement in ["Wide shot", "Close-up", "Medium shot", "Tracking shot", "Aerial shot", "Handheld", "POV", "Low angle", "High angle"]:
        if movement in prompt:
            movements.append(movement)

    return {
        "scene_number": scene_index + 1,
        "word_count": len(prompt.split()),
        "shot_count": shot_count,
        "has_proper_ending": not prompt.endswith('.'),
        "transitions": transitions,
        "camera_movements": movements,
        "starts_correctly": prompt.startswith("Multiple shots")
    }



def validate_sequence(results: List[Dict[str, Any]]) -> Dict:
    """시퀀스 검증"""
    total_words = sum(r["metadata"]["word_count"] for r in results)
    avg_length = total_words // len(results) if results else 0

    # 포멧 확인
    format_checks = all(r["metadata"]["starts_correctly"] for r in results)

    
    return {
        "total_scenes": len(results),
        "avg_length": avg_length,
        "format_check": "모두 통과" if format_checks else "일부 수정 필요",
        "total_shots": sum(r["metadata"]["shot_count"] for r in results)
    }
