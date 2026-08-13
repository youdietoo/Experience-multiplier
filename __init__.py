import unrealsdk

from mods_base import SliderOption, build_mod, hook
from unrealsdk.hooks import Type


XP_DEFINITION_CLASS = "AttributeInitializationDefinition"
XP_DEFINITION_PATH = "GD_Balance_Experience.Formulas.Init_EnemyExperience_PerPlaythrough"

original_baserates = {}


xp_multiplier_slider = SliderOption(
    identifier="XP Multiplier",
    value=1,
    min_value=1,
    max_value=10,
    description="Multiplier for enemy, mission, and discovery experience rewards.",
)


def get_xp_multiplier() -> float:
    return float(xp_multiplier_slider.value)


def get_xp_definition():
    try:
        return unrealsdk.find_object(XP_DEFINITION_CLASS, XP_DEFINITION_PATH)
    except Exception as e:
        print("XP definition lookup failed:", repr(e))
        return None


def cache_original_baserates(definition) -> None:
    if original_baserates:
        return

    initialization = definition.ConditionalInitialization
    if initialization is None:
        return

    for conditional in initialization.ConditionalExpressionList:
        try:
            if not conditional.Expressions:
                continue
            if conditional.BaseValueIfTrue is None:
                continue

            playthrough = int(conditional.Expressions[0].ConstantOperand2)
            base_xp = float(conditional.BaseValueIfTrue.BaseValueConstant)
            original_baserates[playthrough] = base_xp

        except Exception as e:
            print("XP cache error:", repr(e))


def update_enemy_xp_multiplier() -> None:
    try:
        definition = get_xp_definition()

        if definition is None:
            return

        cache_original_baserates(definition)
        multiplier = get_xp_multiplier()
        initialization = definition.ConditionalInitialization
        if initialization is None:
            return

        for conditional in initialization.ConditionalExpressionList:
            if not conditional.Expressions:
                continue
            if conditional.BaseValueIfTrue is None:
                continue

            playthrough = int(conditional.Expressions[0].ConstantOperand2)
            if playthrough not in original_baserates:
                continue

            conditional.BaseValueIfTrue.BaseValueConstant = (original_baserates[playthrough] * multiplier)

    except Exception as e:
        print("XP multiplier update failed:", repr(e))


def reset_enemy_xp_multiplier() -> None:
    try:
        definition = get_xp_definition()
        if definition is None:
            return

        initialization = definition.ConditionalInitialization
        if initialization is None:
            return

        for conditional in initialization.ConditionalExpressionList:
            if not conditional.Expressions:
                continue
            if conditional.BaseValueIfTrue is None:
                continue

            playthrough = int(conditional.Expressions[0].ConstantOperand2)
            if playthrough not in original_baserates:
                continue

            conditional.BaseValueIfTrue.BaseValueConstant = (original_baserates[playthrough])

    except Exception as e:
        print("XP multiplier reset failed:", repr(e))


def on_xp_multiplier_changed(_option: SliderOption, _new_value: float) -> None:
    update_enemy_xp_multiplier()


xp_multiplier_slider.set_on_change(on_xp_multiplier_changed)


@hook("WillowGame.WillowPlayerController:GetMissionDescriptionForUI", Type.PRE,)
def get_mission_description_for_ui(_obj, args, _ret, _func,):
    try:
        mission_def = args.MissionDef

        if not mission_def:
            return

        multiplier = get_xp_multiplier()

        for reward in (mission_def.Reward, mission_def.AlternativeReward):
            if not reward:
                continue

            xp = reward.ExperienceRewardPercentage

            if not xp:
                continue

            xp.BaseValueScaleConstant = multiplier

    except Exception as e:
        print("Mission XP error:", repr(e))


@hook("WillowGame.WillowPlayerController:ServerAwardExperienceForWorldDiscovery", Type.PRE)
def award_world_discovery(obj, args, ret, func):
    try:
        discovery_area = args.DiscoveryArea

        if not discovery_area:
            return

        multiplier = get_xp_multiplier()
        xp_multiplier = discovery_area.ExperienceRewardMultiplier

        if not xp_multiplier:
            return

        xp_multiplier.BaseValueScaleConstant = multiplier

    except Exception as e:
        print("Discovery XP error:", repr(e))


def on_disable() -> None:
    reset_enemy_xp_multiplier()


mod = build_mod(
    options=[xp_multiplier_slider],
    on_disable=on_disable
)


update_enemy_xp_multiplier()
