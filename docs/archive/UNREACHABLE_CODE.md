# Unreachable Code Analysis

**Agent 5: Dead Code Hunter**

**Total files analyzed:** 314

## 1. Code After Terminating Statements

**Unreachable blocks found:** 2

### 1. `isaac/commands/msg/run.py:364`

- **Location:** Line 364 in `_extract_executable_command`
- **Reason:** Code after return
- **Lines affected:** 27

```python
    """Display a single message in full detail."""
    print("=" * 70)
    print(f"Message ID: {message['id']}")
    print(f"Type: {message['message_type']}")
...
```

**Recommendation:** Delete or fix control flow

---

### 2. `isaac/bubbles/manager.py:415`

- **Location:** Line 415 in `suspend_bubble > except`
- **Reason:** Code after return
- **Lines affected:** 20

```python
            if suspend_processes:
                # Attempt to suspend relevant processes
                suspended_pids = []
                for proc_info in bubble.running_processes:
...
```

**Recommendation:** Delete or fix control flow

---


## 2. Potentially Unused Private Functions

**Files with uncalled private functions:** 185

**Note:** These are private functions (starting with `_`) that don't appear to be called within their own module. They may still be called from other modules or used as callbacks.

### `isaac/adapters/powershell_adapter.py`

- `_detect_powershell()`

### `isaac/ai/base.py`

- `_setup()`

### `isaac/ai/claude_client.py`

- `_convert_messages()`
- `_convert_tools()`

### `isaac/ai/collections_core.py`

- `_add_pattern()`
- `_chunk_generic()`
- `_chunk_javascript_regex()`
- `_chunk_python_ast()`
- `_compute_file_hash()`
- `_load_patterns()`
- `_load_state()`
- `_notify_progress()`
- `_process_updates()`
- `_save_state()`

### `isaac/ai/config_manager.py`

- `_load_or_create()`

### `isaac/ai/cost_optimizer.py`

- `_check_and_generate_alerts()`
- `_get_limit_status()`
- `_initialize_cost_data()`
- `_load_cost_data()`
- `_save_cost_data()`

### `isaac/ai/query_classifier.py`

- `_looks_like_path()`

### `isaac/ai/rag_engine.py`

- `_build_context()`
- `_direct_query()`
- `_rag_query()`
- `_search_codebase()`

### `isaac/ai/router.py`

- `_calculate_budget_health_score()`
- `_check_cost_limit()`
- `_get_fallback_order()`
- `_init_clients()`
- `_load_config()`
- `_update_performance_stats()`
- `_update_stats()`

### `isaac/ai/routing_config.py`

- `_merge_with_defaults()`
- `_save_config()`

### `isaac/ai/session_manager.py`

- `_create_session()`
- `_generate_session_id()`
- `_load_sessions()`
- `_rotate_session()`
- `_save_sessions()`

### `isaac/ai/task_analyzer.py`

- `_calculate_confidence()`
- `_can_handle_complexity()`
- `_default_analysis()`
- `_detect_complexity()`
- `_detect_task_type()`
- `_estimate_cost()`
- `_estimate_tokens()`
- `_explain_recommendation()`
- `_get_fallback_providers()`
- `_get_latest_user_message()`
- `_load_provider_capabilities()`
- `_select_provider()`

### `isaac/ai/task_planner.py`

- `_get_ai_fix_suggestion()`

### `isaac/ai/unified_chat.py`

- `_detect_defaults()`
- `_detect_mode()`
- `_handle_direct()`
- `_handle_rag()`
- `_handle_refactor()`
- `_init_components()`

### `isaac/ai/xai_client.py`

- `_call_api()`
- `_call_api_with_messages()`
- `_call_api_with_system_prompt()`

### `isaac/ambient/proactive_suggester.py`

- `_background_analysis()`
- `_clean_expired_suggestions()`
- `_generate_contextual_suggestions()`
- `_generate_error_suggestions()`
- `_generate_pattern_suggestions()`
- `_load_suggestions()`
- `_save_suggestions()`

### `isaac/ambient/workflow_learner.py`

- `_detect_command_patterns()`
- `_detect_workflow_patterns()`
- `_extract_command_sequences()`
- `_generate_suggestions()`
- `_generate_workflow_tags()`
- `_load_existing_patterns()`
- `_normalize_timestamp()`
- `_save_patterns()`
- `_update_patterns()`

### `isaac/analytics/code_quality_tracker.py`

- `_analyze_generic_file()`
- `_analyze_python_file()`
- `_calculate_complexity()`
- `_calculate_maintainability()`
- `_calculate_quality_score()`
- `_count_docstrings()`
- `_generate_quality_insights()`

### `isaac/analytics/dashboard_builder.py`

- `_create_learning_dashboard()`
- `_create_overview_dashboard()`
- `_create_productivity_dashboard()`
- `_create_quality_dashboard()`
- `_create_team_dashboard()`
- `_fetch_insights_data()`
- `_fetch_learning_data()`
- `_fetch_productivity_data()`
- `_fetch_quality_data()`
- `_fetch_team_data()`
- `_fetch_widget_data()`
- `_render_chart_widget()`
- `_render_list_widget()`
- `_render_metric_widget()`
- `_render_table_widget()`
- `_render_widget()`

### `isaac/analytics/database.py`

- `_get_connection()`
- `_init_database()`

### `isaac/analytics/learning_tracker.py`

- `_generate_learning_insights()`
- `_get_top_learnings()`

### `isaac/analytics/productivity_tracker.py`

- `_generate_insights()`
- `_load_baseline_metrics()`

### `isaac/analytics/report_exporter.py`

- `_export_csv()`
- `_export_dashboard_html()`
- `_export_html()`
- `_export_json()`
- `_export_markdown()`
- `_generate_full_report()`

### `isaac/analytics/team_tracker.py`

- `_generate_team_insights()`
- `_get_top_contributors()`

### `isaac/arvr/gesture_api.py`

- `_calculate_confidence()`
- `_initialize_default_patterns()`
- `_trigger_handlers()`

### `isaac/arvr/multimodal_input.py`

- `_add_input()`
- `_check_patterns()`
- `_initialize_default_patterns()`
- `_trigger_pattern_handlers()`

### `isaac/arvr/platform_adapter.py`

- `_trigger_event()`

### `isaac/arvr/prototype_mode.py`

- `_buffer_to_string()`
- `_clear_buffer()`
- `_demo_gesture()`
- `_demo_layout()`
- `_draw_box()`
- `_draw_line()`
- `_draw_text()`
- `_render_layout_node()`
- `_render_object()`
- `_set_pixel()`

### `isaac/bubbles/manager.py`

- `_get_background_jobs()`
- `_get_environment()`
- `_get_git_branch()`
- `_get_git_status()`
- `_get_open_files()`
- `_get_recent_commands()`
- `_get_running_processes()`
- `_get_system_info()`
- `_save_bubble()`

### `isaac/commands/ambient/ambient_command.py`

- `_analyze_history()`
- `_delete_pattern()`
- `_get_help_text()`
- `_learn_from_history()`
- `_list_patterns()`
- `_manage_patterns()`
- `_show_help()`
- `_show_pattern()`
- `_show_stats()`
- `_show_suggestions()`

### `isaac/commands/analytics/analytics_command.py`

- `_analyze_file()`
- `_clear_old_data()`
- `_dashboard()`
- `_disable()`
- `_enable()`
- `_export()`
- `_help()`
- `_insights()`
- `_learning_report()`
- `_list_dashboards()`
- `_productivity_report()`
- `_quality_report()`
- `_summary()`
- `_team_report()`

### `isaac/commands/arvr/arvr_command.py`

- `_cmd_demo()`
- `_cmd_gesture()`
- `_cmd_layout()`
- `_cmd_multimodal()`
- `_cmd_platform()`
- `_cmd_status()`
- `_cmd_workspace()`
- `_gesture_stats()`
- `_layout_list()`
- `_multimodal_stats()`
- `_platform_status()`
- `_show_help()`
- `_workspace_list()`

### `isaac/commands/backup.py`

- `_confirm_backup()`
- `_parse_args()`
- `_perform_backup()`
- `_prompt_destination()`
- `_resolve_path()`
- `_suggest_similar_paths()`

### `isaac/commands/bubble/bubble_command.py`

- `_create_bubble()`
- `_delete_bubble()`
- `_export_bubble()`
- `_get_help_text()`
- `_import_bubble()`
- `_list_bubbles()`
- `_resume_bubble()`
- `_show_bubble_info()`
- `_show_current_bubble()`
- `_show_help()`
- `_suspend_bubble()`

### `isaac/commands/bubble/run.py`

- `_create_bubble()`
- `_create_bubble_version()`
- `_delete_bubble()`
- `_export_bubble()`
- `_format_timestamp()`
- `_import_bubble()`
- `_list_bubble_versions()`
- `_list_bubbles()`
- `_restore_bubble()`
- `_resume_bubble()`
- `_show_bubble()`
- `_suspend_bubble()`

### `isaac/commands/config.py`

- `_check_ai_status()`
- `_check_cloud_status()`
- `_get_version()`
- `_launch_console()`
- `_set_config()`
- `_show_ai_details()`
- `_show_cloud_details()`
- `_show_overview()`
- `_show_plugins()`
- `_show_status()`

### `isaac/commands/help.py`

- `_search_commands()`
- `_show_backup_help()`
- `_show_category_help()`
- `_show_list_help()`
- `_show_man_page()`
- `_show_meta_commands_help()`
- `_show_overview()`
- `_show_restore_help()`
- `_show_whatis()`

### `isaac/commands/help_unified/run.py`

- `_get_special_manual()`
- `_infer_category()`

### `isaac/commands/learn/learn_command.py`

- `_get_health_bar()`
- `_get_help_text()`
- `_record_feedback()`
- `_reset_learning()`
- `_show_behavior()`
- `_show_dashboard()`
- `_show_help()`
- `_show_metrics()`
- `_show_mistakes()`
- `_show_patterns()`
- `_show_preferences()`
- `_show_stats()`
- `_track_mistake()`

### `isaac/commands/list.py`

- `_list_backups()`
- `_list_history()`

### `isaac/commands/machine/run.py`

- `_create_group()`
- `_discover_machines()`
- `_find_machines()`
- `_format_timestamp()`
- `_list_groups()`
- `_list_machines()`
- `_register_machine()`
- `_show_machine()`
- `_unregister_machine()`
- `_update_status()`

### `isaac/commands/mine/run.py`

- `_associate_file_with_array()`
- `_cast_files_batch()`
- `_create_nugget_name()`
- `_ensure_collection()`
- `_extract_project_name()`
- `_guess_content_type()`
- `_handle_abandon()`
- `_handle_cast()`
- `_handle_claim()`
- `_handle_create()`
- `_handle_deed()`
- `_handle_delete()`
- `_handle_dig()`
- `_handle_drift()`
- `_handle_drop()`
- `_handle_grokbug()`
- `_handle_grokrefactor()`
- `_handle_haul()`
- `_handle_haul_extract()`
- `_handle_info()`
- `_handle_list()`
- `_handle_muck()`
- `_handle_nuggets()`
- `_handle_pan()`
- `_handle_skip()`
- `_handle_stake()`
- `_handle_survey()`
- `_handle_use()`
- `_list_nuggets()`
- `_load_collections_data()`
- `_load_mine_config()`
- `_load_mine_settings()`
- `_load_workspace_collection()`
- `_save_active_collection()`
- `_save_collections_data()`
- `_save_nuggets_from_pipe()`
- `_search_nuggets()`
- `_select_relevant_files()`
- `_show_help()`
- `_show_status()`

### `isaac/commands/pair/pair_command.py`

- `_divide_task()`
- `_end_session()`
- `_get_help_text()`
- `_get_score_bar()`
- `_review_code()`
- `_show_help()`
- `_show_history()`
- `_show_learning()`
- `_show_metrics()`
- `_show_status()`
- `_show_suggestions()`
- `_show_tasks()`
- `_start_session()`
- `_switch_roles()`

### `isaac/commands/pipeline/pipeline_command.py`

- `_analyze_patterns()`
- `_create_pipeline()`
- `_delete_pipeline()`
- `_edit_pipeline()`
- `_export_pipeline()`
- `_get_help_text()`
- `_import_pipeline()`
- `_list_pipelines()`
- `_list_templates()`
- `_run_pipeline()`
- `_show_help()`
- `_show_status()`
- `_show_suggestions()`

### `isaac/commands/plugin/plugin_command.py`

- `_create()`
- `_disable()`
- `_enable()`
- `_featured()`
- `_info()`
- `_install()`
- `_list()`
- `_package()`
- `_search()`
- `_show_help()`
- `_show_installed_info()`
- `_show_registry_info()`
- `_test()`
- `_uninstall()`
- `_update()`
- `_validate()`

### `isaac/commands/resources/resources_command.py`

- `_cmd_alerts()`
- `_cmd_cleanup()`
- `_cmd_costs()`
- `_cmd_export()`
- `_cmd_monitor()`
- `_cmd_optimize()`
- `_cmd_predict()`
- `_cmd_start()`
- `_cmd_stats()`
- `_cmd_stop()`
- `_create_bar()`
- `_help()`

### `isaac/commands/restore.py`

- `_confirm_restore()`
- `_parse_args()`
- `_perform_restore()`
- `_prompt_backup_source()`
- `_resolve_path()`

### `isaac/commands/team/team_command.py`

- `_create_team()`
- `_delete_team()`
- `_import_workspace()`
- `_invite_member()`
- `_list_members()`
- `_list_resources()`
- `_list_teams()`
- `_manage_collections()`
- `_manage_memory()`
- `_manage_patterns()`
- `_manage_permissions()`
- `_manage_pipelines()`
- `_remove_member()`
- `_share_resource()`
- `_share_workspace()`
- `_show_help()`
- `_team_info()`
- `_unshare_resource()`
- `_update_role()`

### `isaac/commands/timemachine/timemachine_command.py`

- `_create_snapshot()`
- `_format_age()`
- `_get_help_text()`
- `_interactive_browse()`
- `_playback_mode()`
- `_restore_to_time()`
- `_search_timeline()`
- `_show_graph()`
- `_show_help()`
- `_show_stats()`
- `_show_timeline()`

### `isaac/commands/update/run.py`

- `_detect_package_manager()`
- `_format_outdated_packages()`
- `_get_npm_outdated()`
- `_get_outdated_packages()`
- `_get_pip_outdated()`
- `_get_yarn_outdated()`
- `_update_npm_packages()`
- `_update_packages()`
- `_update_pip_packages()`
- `_update_yarn_packages()`

### `isaac/core/agentic_orchestrator.py`

- `_analyze_task()`
- `_build_context()`
- `_build_messages()`
- `_build_system_prompt()`
- `_emit_event()`
- `_handle_tool_event()`
- `_select_ai_for_task()`
- `_stream_agentic_loop()`

### `isaac/core/ai_translator.py`

- `_resolve_paths()`

### `isaac/core/aliases.py`

- `_load_aliases()`
- `_save_aliases()`

### `isaac/core/boot_loader.py`

- `_check_ai_provider()`
- `_print_status()`

### `isaac/core/change_queue.py`

- `_init_db()`
- `_init_db_on_conn()`
- `_run()`

### `isaac/core/cli_command_router.py`

- `_handle_internal()`
- `_handle_natural()`
- `_handle_shell()`
- `_handle_task()`

### `isaac/core/command_history.py`

- `_load_history()`
- `_save_history()`

### `isaac/core/command_router.py`

- `_build_chat_preprompt()`
- `_confirm()`
- `_get_tier()`
- `_handle_chat_query()`
- `_handle_config_command()`
- `_handle_meta_command()`
- `_is_natural_language()`
- `_is_quoted_pipe()`
- `_route_device_command()`
- `_track_auto_correction()`
- `_track_command_execution()`
- `_track_user_correction_acceptance()`

### `isaac/core/context_manager.py`

- `_load_context()`
- `_save_context()`

### `isaac/core/fallback_manager.py`

- `_execute_fallback()`
- `_load_state()`
- `_save_state()`

### `isaac/core/file_watcher.py`

- `_run()`

### `isaac/core/flag_parser.py`

- `_flag_expects_value()`
- `_parse_long_flag()`
- `_parse_short_flags()`
- `_resolve_alias()`
- `_validate_flags()`

### `isaac/core/key_manager.py`

- `_check_master_key_override()`
- `_ensure_keys_file()`

### `isaac/core/man_pages.py`

- `_format_man_page()`
- `_generate_synopsis()`
- `_load_commands()`

### `isaac/core/message_queue.py`

- `_init_db()`

### `isaac/core/performance.py`

- `_check_eviction()`

### `isaac/core/pipe_engine.py`

- `_execute_command()`
- `_execute_isaac_command()`
- `_execute_shell_command()`
- `_is_isaac_command()`
- `_parse_pipe_segments()`

### `isaac/core/sandbox_enforcer.py`

- `_create_venv_activation_script()`
- `_create_workspace_collection()`
- `_create_workspace_venv()`
- `_load_config()`
- `_save_workspace_metadata()`

### `isaac/core/session_manager.py`

- `_init_file_history()`
- `_init_learning_system()`
- `_load_config()`
- `_load_session_data()`
- `_save_ai_query_history()`
- `_save_command_history()`
- `_save_config()`
- `_save_preferences()`
- `_upload_file_history()`

### `isaac/core/streaming_executor.py`

- `_emit_event()`
- `_merge_async_generators()`

### `isaac/core/task_manager.py`

- `_execute_task()`
- `_init_db()`
- `_load_tasks_from_db()`
- `_save_task_to_db()`
- `_update_task_in_db()`

### `isaac/core/tier_validator.py`

- `_load_tier_defaults()`

### `isaac/core/unified_fs.py`

- `_local_path()`

### `isaac/core/unix_aliases.py`

- `_translate_piped_command()`
- `_translate_with_arg_mapping()`

### `isaac/core/workspace_integration.py`

- `_get_collections_client()`
- `_get_xai_client()`

### `isaac/core/workspace_sessions.py`

- `_load_workspaces()`
- `_save_workspaces()`

### `isaac/crossplatform/api/rest_api.py`

- `_setup_routes()`

### `isaac/crossplatform/api/webhook_manager.py`

- `_deliver_webhook()`
- `_generate_signature()`
- `_process_delivery_queue()`

### `isaac/crossplatform/api/websocket_api.py`

- `_handle_execute()`
- `_handle_get_context()`
- `_handle_message()`
- `_handle_ping()`
- `_handle_query()`
- `_handle_subscribe()`
- `_handle_unsubscribe()`
- `_send_error()`
- `_send_message()`
- `_setup_handlers()`

### `isaac/crossplatform/bubbles/state_manager.py`

- `_init_database()`

### `isaac/crossplatform/bubbles/universal_bubble.py`

- `_capture_environment()`
- `_capture_file_metadata()`
- `_capture_git_state()`
- `_capture_metadata()`
- `_capture_processes()`
- `_capture_workspace()`
- `_compute_file_hash()`
- `_denormalize_path_var()`
- `_generate_bubble_id()`
- `_get_platform_info()`
- `_normalize_env_value()`
- `_normalize_path()`
- `_restore_environment()`
- `_restore_git_state()`

### `isaac/crossplatform/cloud/cloud_executor.py`

- `_execute_aws()`
- `_execute_azure()`
- `_execute_gcp()`
- `_execute_generic()`
- `_execute_on_cloud()`

### `isaac/crossplatform/cloud/cloud_storage.py`

- `_delete_azure()`
- `_delete_from_provider()`
- `_delete_gcs()`
- `_delete_generic()`
- `_delete_s3()`
- `_download_azure()`
- `_download_from_provider()`
- `_download_gcs()`
- `_download_generic()`
- `_download_s3()`
- `_list_azure()`
- `_list_from_provider()`
- `_list_gcs()`
- `_list_generic()`
- `_list_s3()`
- `_upload_azure()`
- `_upload_gcs()`
- `_upload_generic()`
- `_upload_s3()`
- `_upload_to_provider()`

### `isaac/crossplatform/cloud/remote_workspace.py`

- `_initialize_cloud_workspace()`

### `isaac/crossplatform/mobile/mobile_api.py`

- `_setup_routes()`

### `isaac/crossplatform/mobile/notification_service.py`

- `_process_notification_queue()`
- `_send_apns()`
- `_send_fcm()`
- `_send_to_device()`
- `_should_send()`

### `isaac/crossplatform/offline/cache_manager.py`

- `_evict_if_needed()`
- `_init_database()`

### `isaac/crossplatform/offline/conflict_resolver.py`

- `_merge_text()`
- `_resolve_by_timestamp()`
- `_resolve_local_wins()`
- `_resolve_manual()`
- `_resolve_merge()`
- `_resolve_remote_wins()`

### `isaac/crossplatform/offline/offline_manager.py`

- `_check_connectivity()`
- `_handle_connectivity_change()`
- `_sync_queued_operations()`

### `isaac/crossplatform/offline/sync_queue.py`

- `_init_database()`

### `isaac/crossplatform/web/terminal_emulator.py`

- `_convert_ansi_to_html()`

### `isaac/crossplatform/web/web_server.py`

- `_get_index_html()`
- `_get_terminal_html()`
- `_get_workspace_html()`
- `_setup_routes()`

### `isaac/debugging/auto_investigator.py`

- `_analyze_command_error()`
- `_analyze_error_patterns()`
- `_analyze_file_error()`
- `_analyze_network_error()`
- `_analyze_permission_error()`
- `_analyze_resource_error()`
- `_check_file_permissions()`
- `_check_network_status()`
- `_determine_root_cause()`
- `_find_related_files()`
- `_gather_diagnostics()`
- `_gather_evidence()`
- `_generate_recommendations()`
- `_get_disk_usage()`
- `_get_follow_up_actions()`
- `_get_memory_usage()`
- `_get_process_info()`
- `_get_recent_logs()`
- `_load_error_patterns()`
- `_suggest_fixes()`

### `isaac/debugging/debug_command.py`

- `_generate_debug_summary()`

### `isaac/debugging/debug_history.py`

- `_extract_keywords()`
- `_generate_insights_from_session()`
- `_init_database()`
- `_load_patterns_cache()`
- `_row_to_session()`
- `_update_patterns_from_session()`

### `isaac/debugging/fix_suggester.py`

- `_calculate_confidence_factors()`
- `_categorize_error()`
- `_create_fix_suggestion()`
- `_extract_port_from_error()`
- `_generate_generic_fixes()`
- `_generate_preventive_fixes()`
- `_get_applicable_fixes()`
- `_guess_service_name()`
- `_interpolate_commands()`
- `_load_fix_templates()`
- `_load_platform_fixes()`

### `isaac/debugging/performance_profiler.py`

- `_analyze_performance()`
- `_calculate_average_cpu()`
- `_calculate_average_memory()`
- `_calculate_disk_io()`
- `_calculate_network_io()`
- `_calculate_system_load()`
- `_capture_system_metrics()`
- `_generate_recommendations()`
- `_identify_bottlenecks()`
- `_start_background_monitoring()`

### `isaac/debugging/root_cause_analyzer.py`

- `_build_causal_chain()`
- `_build_causal_graph()`
- `_calculate_hypothesis_confidence()`
- `_create_hypothesis_from_pattern()`
- `_determine_primary_root_cause()`
- `_estimate_fix_complexity()`
- `_gather_contradicting_evidence()`
- `_gather_supporting_evidence()`
- `_generate_diagnostic_hypotheses()`
- `_generate_hypotheses()`
- `_generate_preventive_measures()`
- `_get_recommended_tests()`
- `_identify_systemic_issues()`
- `_load_causal_patterns()`
- `_matches_symptoms()`
- `_refine_hypotheses_deep()`

### `isaac/debugging/test_generator.py`

- `_categorize_error()`
- `_determine_expected_failure()`
- `_generate_access_code()`
- `_generate_assertion_code()`
- `_generate_cleanup_code()`
- `_generate_edge_case_test()`
- `_generate_network_code()`
- `_generate_operation_code()`
- `_generate_regression_test()`
- `_generate_reproduction_steps()`
- `_generate_reproduction_test_code()`
- `_generate_setup_code()`
- `_load_language_patterns()`
- `_load_test_templates()`
- `_map_error_to_exception()`

### `isaac/dragdrop/batch_processor.py`

- `_create_batches()`
- `_process_batch_chunk()`
- `_process_large_batch()`
- `_worker_thread()`

### `isaac/dragdrop/interactive_decision.py`

- `_handle_custom_command()`
- `_select_files_interactively()`

### `isaac/dragdrop/multi_file_detector.py`

- `_analyze_single_file()`
- `_calculate_checksum()`
- `_determine_category()`
- `_is_supported_type()`

### `isaac/dragdrop/progress.py`

- `_animate()`
- `_update_display()`

### `isaac/dragdrop/smart_router.py`

- `_analyze_code_file()`
- `_extract_archive_file()`
- `_handle_analyze_code()`
- `_handle_custom_command()`
- `_handle_extract_archive()`
- `_handle_process_documents()`
- `_handle_skip()`
- `_handle_upload_images()`
- `_handle_view_text()`

### `isaac/images/cloud_storage.py`

- `_calculate_checksum()`
- `_extract_text_from_image()`
- `_format_bytes()`
- `_generate_thumbnail()`
- `_get_image_info()`
- `_load_metadata()`
- `_load_quota_settings()`
- `_save_metadata()`
- `_save_quota_settings()`
- `_upload_thumbnail_to_cloud()`
- `_upload_to_cloud()`

### `isaac/integrations/totalcmd_parser.py`

- `_parse_line()`

### `isaac/integrations/xai_collections.py`

- `_operation_to_document()`

### `isaac/learning/behavior_adjustment.py`

- `_analyze_feedback_for_adjustment()`
- `_create_adjustment_for_negative_feedback()`
- `_create_adjustment_for_positive_feedback()`
- `_get_recent_feedback()`
- `_load_behavior_adjustments()`
- `_load_behavior_profile()`
- `_load_feedback_history()`
- `_save_behavior_adjustments()`
- `_save_behavior_profile()`
- `_save_feedback_history()`

### `isaac/learning/continuous_learning_coordinator.py`

- `_check_learning_health()`
- `_consolidate_patterns_if_needed()`
- `_coordination_loop()`
- `_generate_and_analyze_metrics()`
- `_run_coordination_cycle()`
- `_run_learning_optimization()`
- `_sync_cross_component_insights()`

### `isaac/learning/learning_metrics.py`

- `_calculate_improvement_trend()`
- `_calculate_learning_health_score()`
- `_generate_insights()`
- `_generate_recommendations()`
- `_load_learning_insights()`
- `_load_metrics_history()`
- `_save_learning_insights()`
- `_save_metrics_history()`

### `isaac/learning/mistake_learner.py`

- `_background_learning()`
- `_conditions_match()`
- `_extract_trigger_conditions()`
- `_init_database()`
- `_load_patterns()`
- `_mark_mistakes_learned()`
- `_save_patterns()`

### `isaac/learning/performance_analytics.py`

- `_calculate_baselines()`
- `_check_for_performance_issues()`
- `_load_performance_data()`
- `_save_alerts()`
- `_save_performance_data()`

### `isaac/learning/user_preference_learner.py`

- `_analyze_communication_style()`
- `_analyze_response_preference()`
- `_analyze_technical_level()`
- `_calculate_context_match()`
- `_calculate_observation_weight()`
- `_get_or_create_pattern()`
- `_initialize_user_profile()`
- `_load_learned_patterns()`
- `_load_user_preferences()`
- `_save_learned_patterns()`
- `_save_user_preferences()`

### `isaac/memory/database.py`

- `_calculate_checksum()`
- `_init_db()`

### `isaac/models/task_history.py`

- `_find_task()`

### `isaac/monitoring/base_monitor.py`

- `_perform_check()`
- `_run_loop()`
- `_send_message()`

### `isaac/monitoring/code_monitor.py`

- `_check_outdated_dependencies()`
- `_check_python_linting()`
- `_check_test_failures()`
- `_perform_check()`

### `isaac/monitoring/system_monitor.py`

- `_check_disk_space()`
- `_check_memory_usage()`
- `_check_system_updates()`
- `_perform_check()`

### `isaac/nlscript/explainer.py`

- `_assess_complexity()`
- `_basic_explanation()`
- `_build_explanation_prompt()`
- `_parse_explanation_response()`
- `_parse_functions()`

### `isaac/nlscript/generator.py`

- `_build_generation_prompt()`
- `_generate_basic_script()`
- `_parse_generation_response()`
- `_parse_metadata()`
- `_save_history()`
- `_save_script()`

### `isaac/nlscript/scheduler.py`

- `_ai_parse_schedule()`
- `_calculate_next_run()`
- `_cron_to_human()`
- `_init_patterns()`
- `_parse_daily()`
- `_parse_schedule()`
- `_parse_time()`
- `_parse_weekly()`
- `_validate_cron()`

### `isaac/nlscript/templates.py`

- `_load_builtin_templates()`
- `_load_custom_templates()`
- `_save_custom_templates()`

### `isaac/nlscript/translator.py`

- `_build_translation_prompt()`
- `_get_cache_key()`
- `_parse_ai_response()`
- `_parse_cached_result()`
- `_simple_translation()`

### `isaac/nlscript/validator.py`

- `_check_best_practices()`
- `_check_safety()`
- `_init_dangerous_patterns()`
- `_run_shellcheck()`
- `_strict_validation()`
- `_validate_syntax()`

### `isaac/orchestration/load_balancer.py`

- `_calculate_capacity_factor()`
- `_get_candidates()`
- `_get_performance_factor()`
- `_least_load_selection()`
- `_performance_based_selection()`
- `_random_selection()`
- `_resource_aware_selection()`
- `_round_robin_selection()`
- `_weighted_least_load_selection()`

### `isaac/orchestration/registry.py`

- `_load_registry()`
- `_save_registry()`

### `isaac/orchestration/remote.py`

- `_execute_remote_command()`

### `isaac/pairing/code_review.py`

- `_get_condition_complexity()`
- `_get_function_length()`
- `_init_database()`
- `_load_review_rules()`
- `_review_python_ast()`
- `_review_python_code()`
- `_save_suggestion()`

### `isaac/pairing/pair_metrics.py`

- `_calculate_code_quality_score()`
- `_calculate_collaboration_score()`
- `_calculate_learning_score()`
- `_calculate_productivity_score()`
- `_get_session_events()`
- `_init_database()`
- `_save_metrics()`

### `isaac/pairing/pair_mode.py`

- `_init_database()`
- `_save_session()`

### `isaac/pairing/pairing_learner.py`

- `_analyze_recent_interactions()`
- `_background_learning()`
- `_context_matches()`
- `_init_database()`
- `_learn_formatting_preferences()`
- `_learn_naming_conventions()`
- `_learn_structure_preferences()`
- `_load_patterns()`
- `_save_style_preference()`
- `_update_style_preference()`

### `isaac/pairing/suggestion_system.py`

- `_analyze_for_optimizations()`
- `_init_database()`
- `_is_boolean_search_loop()`
- `_is_simple_append_loop()`
- `_load_suggestion_patterns()`
- `_save_suggestion()`

### `isaac/pairing/task_division.py`

- `_dependencies_completed()`
- `_divide_bug_fix_task()`
- `_divide_feature_task()`
- `_divide_generic_task()`
- `_divide_refactoring_task()`
- `_divide_testing_task()`
- `_init_database()`
- `_save_task()`

### `isaac/patterns/enhanced_anti_patterns.py`

- `_add_docstring_fix()`
- `_analyze_class()`
- `_analyze_function()`
- `_analyze_module()`
- `_apply_general_rules()`
- `_calculate_complexity_score()`
- `_calculate_maintainability_index()`
- `_calculate_node_complexity()`
- `_calculate_quality_score()`
- `_check_bare_except()`
- `_check_function_too_long()`
- `_check_god_class()`
- `_check_high_complexity()`
- `_check_imports_not_at_top()`
- `_check_missing_docstring()`
- `_check_missing_type_hints()`
- `_check_mutable_defaults()`
- `_check_too_many_parameters()`
- `_check_unused_imports()`
- `_create_detection_from_result()`
- `_deduplicate_anti_patterns()`
- `_fix_mutable_defaults()`
- `_load_builtin_rules()`
- `_load_custom_rules()`

### `isaac/patterns/pattern_applier.py`

- `_add_docstring_to_class()`
- `_add_docstring_to_function()`
- `_analyze_code_for_improvements()`
- `_analyze_imports()`
- `_analyze_naming()`
- `_analyze_node_for_patterns()`
- `_analyze_simplifications()`
- `_calculate_complexity()`
- `_calculate_nesting_level()`
- `_class_pattern_match()`
- `_convert_to_dataclass()`
- `_detect_language()`
- `_function_pattern_match()`
- `_get_node_source()`
- `_has_docstring()`
- `_has_type_hints()`
- `_loop_pattern_match()`
- `_parse_code()`
- `_pattern_matches_node()`
- `_simplify_nested_loops()`
- `_suggest_list_comprehension()`

### `isaac/patterns/pattern_documentation.py`

- `_extract_pattern_info()`
- `_extract_usage_stats()`
- `_fill_template()`
- `_format_examples()`
- `_generate_alternatives()`
- `_generate_benefits()`
- `_generate_content_sections()`
- `_generate_related_patterns()`
- `_generate_statistics()`
- `_generate_when_to_use()`
- `_get_template_for_category()`
- `_load_builtin_templates()`
- `_load_documentation()`
- `_save_documentation()`

### `isaac/patterns/pattern_evolution.py`

- `_analyze_user_feedback()`
- `_apply_evolution_action()`
- `_background_evolution()`
- `_calculate_evolution_score()`
- `_calculate_performance_trend()`
- `_calculate_usage_trend()`
- `_evaluate_evolution_condition()`
- `_get_recent_usage()`
- `_initialize_default_rules()`
- `_load_evolution_metrics()`
- `_load_evolution_rules()`
- `_load_pattern_variants()`
- `_load_usage_history()`
- `_save_evolution_metrics()`
- `_save_evolution_rules()`
- `_save_pattern_variants()`
- `_save_usage_history()`
- `_update_metrics_for_usage()`
- `_update_running_average()`

### `isaac/patterns/pattern_learner.py`

- `_analyze_class_pattern()`
- `_analyze_function_pattern()`
- `_calculate_code_score()`
- `_calculate_complexity()`
- `_calculate_nesting_level()`
- `_check_class_anti_patterns()`
- `_check_error_handling_anti_patterns()`
- `_check_function_anti_patterns()`
- `_check_loop_anti_patterns()`
- `_check_naming_anti_patterns()`
- `_create_class_pattern()`
- `_create_class_template()`
- `_create_function_pattern()`
- `_create_function_template()`
- `_detect_language()`
- `_extract_class_variables()`
- `_extract_function_variables()`
- `_file_modified_time()`
- `_get_node_source()`
- `_has_docstring()`
- `_has_type_hints()`
- `_learn_async_patterns()`
- `_learn_class_patterns()`
- `_learn_data_structure_patterns()`
- `_learn_error_handling_patterns()`
- `_learn_function_patterns()`
- `_learn_loop_patterns()`
- `_learn_naming_patterns()`
- `_learn_style_patterns()`
- `_load_patterns()`
- `_parse_code()`
- `_save_patterns()`

### `isaac/patterns/team_sharing.py`

- `_background_sync()`
- `_load_contributions()`
- `_load_repositories()`
- `_record_contribution()`
- `_save_contributions()`
- `_save_repositories()`
- `_sync_contributions()`
- `_sync_repositories()`

### `isaac/pipelines/executor.py`

- `_execute_command()`
- `_execute_condition()`
- `_execute_loop()`
- `_execute_notification()`
- `_execute_parallel()`
- `_execute_script()`
- `_execute_wait()`
- `_substitute_variables()`

### `isaac/pipelines/manager.py`

- `_load_all_pipelines()`
- `_save_pipeline()`

### `isaac/pipelines/models.py`

- `_step_from_dict()`
- `_step_to_dict()`

### `isaac/pipelines/pattern_learner.py`

- `_create_single_command_pipeline()`
- `_create_workflow_pipeline()`
- `_extract_sequences()`
- `_find_command_patterns()`
- `_find_workflow_patterns()`
- `_generate_suggestions()`
- `_group_similar_sequences()`
- `_suggest_command_name()`
- `_suggest_workflow_name()`

### `isaac/pipelines/runner.py`

- `_build_dependency_graph()`
- `_build_reverse_dependencies()`
- `_dependencies_satisfied()`
- `_execute_pipeline()`
- `_execute_step_with_retries()`

### `isaac/plugins/examples/command_logger.py`

- `_log_entry()`
- `_save_logs()`

### `isaac/plugins/plugin_manager.py`

- `_create_context()`
- `_load_installed_plugins()`
- `_load_plugin()`
- `_register_plugin_hooks()`
- `_save_installed_plugins()`
- `_unregister_plugin_hooks()`

### `isaac/plugins/plugin_registry.py`

- `_download_from_url()`
- `_fetch_registry()`
- `_get_builtin_registry()`
- `_load_cache()`
- `_needs_update()`
- `_save_cache()`
- `_verify_checksum()`

### `isaac/plugins/plugin_security.py`

- `_file_guard()`
- `_import_guard()`
- `_resource_limits()`
- `_timeout()`

### `isaac/queue/command_queue.py`

- `_init_db()`

### `isaac/queue/sync_worker.py`

- `_is_cloud_available()`
- `_sync_batch()`
- `_sync_command()`
- `_sync_loop()`

### `isaac/resources/alerts.py`

- `_create_default_rules()`
- `_load_data()`
- `_monitor_loop()`
- `_save_data()`

### `isaac/resources/cleanup.py`

- `_add_result()`
- `_load_history()`
- `_save_history()`

### `isaac/resources/cost_tracker.py`

- `_load_data()`
- `_save_data()`

### `isaac/resources/monitor.py`

- `_monitor_loop()`

### `isaac/resources/optimizer.py`

- `_add_suggestion()`
- `_analyze_browser_caches()`
- `_analyze_docker()`
- `_analyze_log_files()`
- `_analyze_node_modules()`
- `_analyze_old_files()`
- `_analyze_package_caches()`
- `_analyze_temp_files()`

### `isaac/resources/predictor.py`

- `_calculate_trend()`
- `_generate_recommendation()`

### `isaac/runtime/dispatcher.py`

- `_detect_execution_mode()`
- `_execute_background()`
- `_get_task_manager()`
- `_run_handler()`

### `isaac/runtime/manifest_loader.py`

- `_load_json_schema()`

### `isaac/scheduler/cron_manager.py`

- `_run_loop()`

### `isaac/team/manager.py`

- `_init_db()`

### `isaac/team/permission_system.py`

- `_init_db()`

### `isaac/team/team_memory.py`

- `_init_db()`

### `isaac/timemachine/time_machine.py`

- `_cleanup_old_snapshots()`
- `_format_age()`
- `_load_timeline()`
- `_save_timeline()`
- `_start_auto_snapshot()`

### `isaac/timemachine/timeline_browser.py`

- `_confirm_restore()`
- `_filter_entries()`
- `_format_age()`
- `_show_entry_info()`

### `isaac/tools/code_analysis.py`

- `_analyze_javascript()`
- `_analyze_python()`
- `_detect_language()`
- `_extract_classes()`
- `_extract_functions()`
- `_extract_imports()`
- `_get_base_name()`
- `_get_decorator_name()`
- `_should_include()`

### `isaac/tools/code_search.py`

- `_is_text_file()`

### `isaac/tools/file_ops.py`

- `_detect_language()`

### `isaac/tools/registry.py`

- `_extract_capabilities()`
- `_register_tool()`

### `isaac/tools/shell_exec.py`

- `_get_shell_adapter()`
- `_get_tier_validator()`
- `_is_safe_command()`

### `isaac/ui/_archived/advanced_input.py`

- `_get_char()`
- `_handle_backspace()`
- `_handle_tab_completion()`
- `_insert_character()`
- `_move_cursor_left()`
- `_move_cursor_right()`
- `_navigate_history()`
- `_redraw_input()`

### `isaac/ui/_archived/terminal_control.py`

- `_calculate_header_hash()`
- `_clear_screen()`
- `_draw_status_bar()`
- `_generate_session_id()`
- `_get_ip_address()`
- `_monitor_statuses()`
- `_position_cursor_for_input()`
- `_save_config()`
- `_setup_scroll_region()`
- `_start_status_monitor()`
- `_update_ai_status()`
- `_update_cloud_status()`
- `_update_system_stats()`
- `_update_terminal_size()`
- `_update_vpn_status()`
- `_wrap_text()`

### `isaac/ui/config_console.py`

- `_()`
- `_create_ui()`
- `_get_defaults()`
- `_handle_cancel()`
- `_handle_save()`
- `_load_settings()`
- `_run_non_interactive_fallback()`
- `_run_text_fallback()`
- `_save_settings()`
- `_validate_settings()`
- `_validate_settings_from_dict()`

### `isaac/ui/header_display.py`

- `_build_header_lines()`
- `_draw_header()`
- `_format_session_time()`
- `_get_cloud_indicator()`
- `_get_tier_indicator()`

### `isaac/ui/inline_suggestions.py`

- `_default_context()`

### `isaac/ui/permanent_shell.py`

- `_()`
- `_create_key_bindings()`
- `_detect_project_type()`
- `_detect_shell()`
- `_execute_next_in_sequence()`
- `_get_prediction_context()`
- `_get_prompt()`
- `_get_time_of_day()`
- `_handle_multi_step_prediction()`
- `_learn_from_command()`
- `_learn_from_correction()`
- `_load_command_history()`
- `_print_welcome()`
- `_setup_sync_callback()`

### `isaac/ui/predictive_completer.py`

- `_commands_similar()`
- `_find_similar_commands()`
- `_get_context_key()`
- `_learn_command_prefixes()`
- `_load_patterns()`
- `_save_patterns()`
- `_update_patterns()`

### `isaac/ui/progress_indicator.py`

- `_animate_spinner()`
- `_get_bar_display()`
- `_get_dots_display()`
- `_get_percent_display()`
- `_get_spinner_display()`
- `_get_text_display()`

### `isaac/ui/prompt_handler.py`

- `_get_tier_indicator()`
- `_scroll_output_area()`

### `isaac/ui/splash_screen.py`

- `_show_ascii_logo()`
- `_show_loading_messages()`
- `_show_war_games_reference()`

### `isaac/ui/streaming_display.py`

- `_emit_event()`

### `isaac/voice/multi_language.py`

- `_cache_result()`
- `_load_cache()`
- `_load_language_configs()`
- `_load_models()`
- `_load_services()`
- `_load_voice_patterns()`
- `_normalize_lang_code()`
- `_rule_based_detection()`
- `_save_cache()`
- `_translate_with_service()`

### `isaac/voice/speech_to_text.py`

- `_load_engines()`
- `_load_model()`
- `_load_shortcuts()`
- `_process_commands()`
- `_save_shortcuts()`

### `isaac/voice/text_to_speech.py`

- `_cleanup_audio_file()`
- `_load_engines()`
- `_play_audio_file()`
- `_process_speech_queue()`
- `_process_speech_request()`

### `isaac/voice/voice_shortcuts.py`

- `_is_context_match()`
- `_load_default_shortcuts()`
- `_load_user_shortcuts()`
- `_match_shortcut_phrases()`
- `_save_user_shortcuts()`

### `isaac/voice/voice_transcription.py`

- `_convert_to_optimal_format()`
- `_format_srt_time()`
- `_get_wav_info()`
- `_load_engines()`
- `_load_model()`
- `_parse_audio_info()`
- `_process_transcription_queue()`

