import unrealsdk

from mods_base import SliderOption, build_mod, hook
from unrealsdk.hooks import Type


XP_DEFINITION_CLASS = "AttributeInitializationDefinition"
XP_DEFINITION_PATH = ("GD_Balance_Experience.Formulas.Init_EnemyExperience_PerPlaythrough")

original_baserates = {}

def get_xp_multiplier() -> float:
    return float(xp_multiplier_slider.value)


def on_xp_multiplier_changed(_option: SliderOption, _new_value: float) -> None:
    update_enemy_xp_multiplier()


xp_multiplier_slider = SliderOption(
    identifier="XP Multiplier",
    value=1,
    min_value=1,
    max_value=10,
    description="Multiplier for enemy, mission, and discovery experience rewards.",
)

xp_multiplier_slider.set_on_change(on_xp_multiplier_changed)

def get_xp_definition():
    return unrealsdk.find_object(XP_DEFINITION_CLASS, XP_DEFINITION_PATH,)


def cache_original_baserates(definition) -> None:
    if original_baserates:
        return

    for conditional in (definition.ConditionalInitialization.ConditionalExpressionList):
        playthrough = int(conditional.Expressions[0].ConstantOperand2)
        base_xp = float(conditional.BaseValueIfTrue.BaseValueConstant)

        original_baserates[playthrough] = base_xp


def update_enemy_xp_multiplier() -> None:
    definition = get_xp_definition()

    if definition is None:
        return

    cache_original_baserates(definition)
    multiplier = get_xp_multiplier()

    for conditional in (definition.ConditionalInitialization.ConditionalExpressionList):
        playthrough = int(conditional.Expressions[0].ConstantOperand2)

        if playthrough not in original_baserates:
            continue

        base_xp = original_baserates[playthrough]
        final_xp = base_xp * multiplier

        conditional.BaseValueIfTrue.BaseValueConstant = final_xp


def reset_enemy_xp_multiplier() -> None:
    definition = get_xp_definition()

    if definition is None:
        return

    for conditional in (definition.ConditionalInitialization.ConditionalExpressionList):
        playthrough = int(conditional.Expressions[0].ConstantOperand2)

        if playthrough not in original_baserates:
            continue

        conditional.BaseValueIfTrue.BaseValueConstant = (original_baserates[playthrough])


@hook("WillowGame.WillowPlayerController:GetMissionDescriptionForUI", Type.PRE,)
def get_mission_description_for_ui(_obj, args, _ret, _func):
    mission_def = args.MissionDef

    if not mission_def:
        return

    multiplier = get_xp_multiplier()

    for reward in (mission_def.Reward, mission_def.AlternativeReward,):
        if not reward:
            continue

        xp = reward.ExperienceRewardPercentage
        xp.BaseValueScaleConstant = multiplier


@hook("WillowGame.WillowPlayerController:ServerAwardExperienceForWorldDiscovery", Type.PRE)
def award_world_discovery(obj, args, ret, func):
    discovery_area = args.DiscoveryArea

    if not discovery_area:
        return

    multiplier = get_xp_multiplier()

    xp_multiplier = discovery_area.ExperienceRewardMultiplier
    original_scale = xp_multiplier.BaseValueScaleConstant
    xp_multiplier.BaseValueScaleConstant = multiplier


def on_disable() -> None:
    reset_enemy_xp_multiplier()
    original_mission_scales.clear()


mod = build_mod(
    options=[xp_multiplier_slider],
    on_disable=on_disable
)

update_enemy_xp_multiplier()
