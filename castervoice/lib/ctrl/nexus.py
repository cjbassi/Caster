from castervoice.lib.ctrl.grammar_container import GrammarContainer
from castervoice.lib.ctrl.mgr.config.rules_config import RulesActivationConfig
from castervoice.lib.ctrl.mgr.grammar_activator import GrammarActivator
from castervoice.lib.ctrl.mgr.rule_maker.mapping_rule_maker import MappingRuleMaker
from castervoice.lib.dfplus.ccrmerging2.hooks.hooks_runner import HooksRunner
from castervoice.lib.dfplus.merge.mergerule import MergeRule

from castervoice.lib import settings
from castervoice.lib.ctrl.dependencies import DependencyMan
from castervoice.lib.ctrl.mgr.validation.details.ccr_app_validator import AppCCRDetailsValidator
from castervoice.lib.ctrl.mgr.validation.details.ccr_validator import CCRDetailsValidator
from castervoice.lib.ctrl.mgr.validation.details.details_validation_delegator import DetailsValidationDelegator
from castervoice.lib.ctrl.mgr.validation.details.non_ccr_validator import NonCCRDetailsValidator
from castervoice.lib.ctrl.mgr.validation.rules.context_validator import HasContextValidator
from castervoice.lib.ctrl.mgr.validation.rules.mergerule_validator import IsMergeRuleValidator
from castervoice.lib.ctrl.mgr.validation.rules.no_context_validator import HasNoContextValidator
from castervoice.lib.ctrl.mgr.validation.rules.not_noderule_validator import NotNodeRuleValidator
from castervoice.lib.ctrl.mgr.validation.rules.pronunciation_validator import PronunciationAvailableValidator
from castervoice.lib.ctrl.mgr.validation.rules.selfmod_validator import SelfModifyingRuleValidator
from castervoice.lib.ctrl.wsrdf import RecognitionHistoryForWSR
from castervoice.lib.dfplus.ccrmerging2.transformers.gdef_transformer import GlobalDefinitionsRuleTransformer
from castervoice.lib.dfplus.communication import Communicator
from castervoice.lib.dfplus.state.stack import CasterState
from dragonfly.grammar.grammar_base import Grammar
from dragonfly.grammar.recobs import RecognitionHistory
from castervoice.lib.ctrl.mgr.grammar_manager import GrammarManager
from castervoice.lib.ctrl.mgr.loading.content_loader import ContentLoader
from castervoice.lib.ctrl.mgr.validation.rules.rule_validation_delegator import CCRRuleValidationDelegator
from castervoice.lib.dfplus.ccrmerging2.ccrmerger2 import CCRMerger2
from castervoice.lib.dfplus.ccrmerging2.compatibility.simple_compat_checker import SimpleCompatibilityChecker
from castervoice.lib.dfplus.ccrmerging2.merging.classic_merging_strategy import ClassicMergingStrategy
from castervoice.lib.dfplus.ccrmerging2.sorting.config_ruleset_sorter import ConfigRuleSetSorter
from castervoice.lib.ctrl.mgr.loading.file_watcher_observable import FileWatcherObservable
from castervoice.lib.ctrl.mgr.loading.manual_reload_observable import ManualReloadObservable


class Nexus:
    def __init__(self):
        """
        The Nexus is the 'glue code' of Caster. It is where the things reside which
        manage global state. It is also an access point to those things for other
        things which need them. This access should be limited.
        """

        '''CasterState is used for impl of the asynchronous actions'''
        self.state = CasterState()

        '''clipboard dict: used for multi-clipboard in navigation module'''
        self.clip = {}

        '''recognition history: for rules which require "lookback"'''
        if settings.WSR:
            self.history = RecognitionHistoryForWSR(20)
        else:
            self.history = RecognitionHistory(20)
            self.history.register()
        self.state.set_stack_history(self.history)
        self.preserved = None

        '''rpc class for interacting with Caster UI elements via xmlrpclib'''
        self.comm = Communicator()

        '''dependency checker/manager'''
        self.dep = DependencyMan()

        '''grammar for recording macros -- should be moved elsewhere'''
        self.macros_grammar = Grammar("recorded_macros")

        '''the ccrmerger -- only merges MergeRules'''
        self.merger = Nexus._create_merger()

        '''unified loading mechanism for [rules, transformers, examples] 
        from [caster starter locations, user dir]'''
        self._content_loader = ContentLoader()

        '''receives and runs events'''
        hooks_runner = HooksRunner()

        '''the grammar manager -- probably needs to get broken apart more'''
        self._grammar_manager = Nexus._create_grammar_manager(self.merger, self._content_loader, hooks_runner)

        '''ACTION TIME:'''
        self._load_and_register_all_content(hooks_runner)

    def _load_and_register_all_content(self, hooks_runner):
        """
        all rules go to grammar_manager
        all transformers go to merger
        TODO: examples go to both? depends on where we want hook events, eh?
        """
        content = self.content_loader.load_everything()
        [self._grammar_manager.register_rule(rc, d) for rc, d in content.rules]
        self._grammar_manager.load_activation_grammar()
        [self.merger.add_transformer(t) for t in content.transformers]
        [hooks_runner.add_hook(h) for h in content.hooks]

    @staticmethod
    def _create_grammar_manager(merger, content_loader, hooks_runner):
        ccr_rule_validator = CCRRuleValidationDelegator(
            IsMergeRuleValidator(),
            HasNoContextValidator(),
            HasContextValidator(),
            SelfModifyingRuleValidator(),
            NotNodeRuleValidator(),
            PronunciationAvailableValidator()
        )
        details_validator = DetailsValidationDelegator(
            CCRDetailsValidator(),
            AppCCRDetailsValidator(),
            NonCCRDetailsValidator()
        )

        activator = GrammarActivator(lambda rule: isinstance(rule, MergeRule))
        some_setting = True
        observable = FileWatcherObservable()
        if some_setting:
            observable = ManualReloadObservable()
        rule_activation_config = RulesActivationConfig()
        mapping_rule_maker = MappingRuleMaker()
        grammars_container = GrammarContainer()

        '''
            config,
            merger,
            content_loader,
            ccr_rules_validator,
            details_validator,
            reload_observable,
            activator,
            mapping_rule_maker,
            grammars_container,
            hooks_runner,
            always_global_ccr_mode
        '''

        # TODO: need to take care of rdp_mode_exclusion and transformer_exclusion
        return GrammarManager(rule_activation_config, merger, content_loader, ccr_rule_validator, details_validator,
            observable, activator, mapping_rule_maker, grammars_container, hooks_runner, always_global_ccr_mode)

    @staticmethod
    def _create_merger():
        transformers = [GlobalDefinitionsRuleTransformer()]
        sorter = ConfigRuleSetSorter()
        compat_checker = SimpleCompatibilityChecker()
        merge_strategy = ClassicMergingStrategy()

        return CCRMerger2(transformers, sorter, compat_checker, merge_strategy)
