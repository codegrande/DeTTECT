from copy import deepcopy
from datetime import datetime
import xlsxwriter
import simplejson
from generic import *


# Imports for pandas and plotly are because of performance reasons in the function that uses these libraries.


def generate_data_sources_layer(filename, output_filename, layer_name):
    """
    Generates a generic layer for data sources.
    :param filename: the filename of the YAML file containing the data sources administration
    :param output_filename: the output filename defined by the user
    :param layer_name: the name of the Navigator layer
    :param platform: one or multiple values from PLATFORMS constant
    :return:
    """
    my_data_sources, name, systems, exceptions = load_data_sources(filename)

    # Do the mapping between my data sources and MITRE data sources:
    my_techniques = _map_and_colorize_techniques(my_data_sources, systems, exceptions)

    if not layer_name:
        layer_name = 'Data sources ' + name

    platforms = list(set(chain.from_iterable(map(lambda k: k['platform'], systems))))
    layer = get_layer_template_data_sources(layer_name, 'description', platforms)
    layer['techniques'] = my_techniques

    json_string = simplejson.dumps(layer).replace('}, ', '},\n')
    if not output_filename:
        output_filename = create_output_filename('data_sources', name)
    write_file(output_filename, json_string)


def plot_data_sources_graph(filename, output_filename):
    """
    Generates a line graph which shows the improvements on numbers of data sources through time.
    :param filename: the filename of the YAML file containing the data sources administration
    :param output_filename: the output filename defined by the user
    :return:
    """
    my_data_sources, name, _, _ = load_data_sources(filename)

    graph_values = []
    for ds_global, ds_detail in my_data_sources.items():
        for ds in ds_detail['data_source']:
            if ds['date_connected']:
                yyyymm = ds['date_connected'].strftime('%Y-%m')
                graph_values.append({'date': yyyymm, 'count': 1})

    import pandas as pd
    df = pd.DataFrame(graph_values).groupby('date', as_index=False)[['count']].sum()
    df['cumcount'] = df['count'].cumsum()

    if not output_filename:
        output_filename = 'graph_data_sources'
    elif output_filename.endswith('.html'):
        output_filename = output_filename.replace('.html', '')
    output_filename = get_non_existing_filename('output/' + output_filename, 'html')

    import plotly.graph_objs as go
    import plotly.offline as offline
    offline.plot(
        {'data': [go.Scatter(x=df['date'], y=df['cumcount'])],
         'layout': go.Layout(title="# of data sources for " + name)},
        filename=output_filename, auto_open=False
    )
    print("File written:   " + output_filename)


def export_data_source_list_to_excel(filename, output_filename, eql_search=False):
    """
    Makes an overview of all MITRE ATT&CK data sources (via techniques) and lists which data sources are present
    in the YAML administration including all properties and data quality score.
    :param filename: the filename of the YAML file containing the data sources administration
    :param output_filename: the output filename defined by the user
    :param eql_search: specify if an EQL search was performed which may have resulted in missing ATT&CK data sources
    :return:
    """
    # pylint: disable=unused-variable
    my_data_sources, name, _, _ = load_data_sources(filename, filter_empty_scores=False)
    my_data_sources = dict(sorted(my_data_sources.items(), key=lambda kv: kv[0], reverse=False))
    if not output_filename:
        output_filename = 'data_sources'
    elif output_filename.endswith('.xlsx'):
        output_filename = output_filename.replace('.xlsx', '')
    excel_filename = get_non_existing_filename('output/' + output_filename, 'xlsx')
    workbook = xlsxwriter.Workbook(excel_filename)
    worksheet = workbook.add_worksheet('Data sources')

    # Formatting:
    format_bold_left = workbook.add_format({'align': 'left', 'bold': True})
    format_title = workbook.add_format({'align': 'left', 'bold': True, 'font_size': '14'})
    format_center_valign_top = workbook.add_format({'align': 'center', 'valign': 'top'})
    wrap_text = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    valign_top = workbook.add_format({'valign': 'top'})
    no_score = workbook.add_format({'valign': 'top', 'align': 'center'})
    dq_score_0 = workbook.add_format({'valign': 'top', 'align': 'center'})
    dq_score_1 = workbook.add_format({'valign': 'top', 'align': 'center', 'bg_color': COLOR_DS_25p})
    dq_score_2 = workbook.add_format({'valign': 'top', 'align': 'center', 'bg_color': COLOR_DS_50p})
    dq_score_3 = workbook.add_format({'valign': 'top', 'align': 'center', 'bg_color': COLOR_DS_75p, 'font_color': '#ffffff'})
    dq_score_4 = workbook.add_format({'valign': 'top', 'align': 'center', 'bg_color': COLOR_DS_99p, 'font_color': '#ffffff'})
    dq_score_5 = workbook.add_format({'valign': 'top', 'align': 'center', 'bg_color': COLOR_DS_100p, 'font_color': '#ffffff'})

    # Title
    worksheet.write(0, 0, 'Data sources for ' + name, format_title)

    # Header columns
    worksheet.write(2, 0, 'Data source name', format_bold_left)
    worksheet.write(2, 1, 'Applicable to', format_bold_left)
    worksheet.write(2, 2, 'Date registered', format_bold_left)
    worksheet.write(2, 3, 'Date connected', format_bold_left)
    worksheet.write(2, 4, 'Products', format_bold_left)
    worksheet.write(2, 5, 'Comment', format_bold_left)
    worksheet.write(2, 6, 'Available for data analytics', format_bold_left)
    worksheet.write(2, 7, 'DQ: device completeness', format_bold_left)
    worksheet.write(2, 8, 'DQ: data field completeness', format_bold_left)
    worksheet.write(2, 9, 'DQ: timeliness', format_bold_left)
    worksheet.write(2, 10, 'DQ: consistency', format_bold_left)
    worksheet.write(2, 11, 'DQ: retention', format_bold_left)
    worksheet.write(2, 12, 'DQ: score', format_bold_left)

    worksheet.set_column(0, 0, 35)
    worksheet.set_column(1, 1, 18)
    worksheet.set_column(2, 3, 15)
    worksheet.set_column(4, 4, 35)
    worksheet.set_column(5, 5, 50)
    worksheet.set_column(6, 6, 24)
    worksheet.set_column(7, 8, 25)
    worksheet.set_column(9, 11, 15)
    worksheet.set_column(12, 12, 10)

    # Putting the data sources data:
    y = 3

    for ds_global, ds_detail in my_data_sources.items():

        for ds in ds_detail['data_source']:
            worksheet.write(y, 0, ds_global, valign_top)

            date_registered = ds['date_registered'].strftime('%Y-%m-%d') if isinstance(ds['date_registered'], datetime) else ds['date_registered']
            date_connected = ds['date_connected'].strftime('%Y-%m-%d') if isinstance(ds['date_connected'], datetime) else ds['date_connected']

            worksheet.write(y, 1, ', '.join(ds['applicable_to']), wrap_text)
            worksheet.write(y, 2, str(date_registered).replace('None', ''), valign_top)
            worksheet.write(y, 3, str(date_connected).replace('None', ''), valign_top)
            worksheet.write(y, 4, ', '.join(ds['products']).replace('None', ''), valign_top)
            worksheet.write(y, 5, ds['comment'][:-1] if ds['comment'].endswith('\n') else ds['comment'], wrap_text)
            worksheet.write(y, 6, str(ds['available_for_data_analytics']), valign_top)
            worksheet.write(y, 7, ds['data_quality']['device_completeness'], format_center_valign_top)
            worksheet.write(y, 8, ds['data_quality']['data_field_completeness'], format_center_valign_top)
            worksheet.write(y, 9, ds['data_quality']['timeliness'], format_center_valign_top)
            worksheet.write(y, 10, ds['data_quality']['consistency'], format_center_valign_top)
            worksheet.write(y, 11, ds['data_quality']['retention'], format_center_valign_top)

            score = 0
            score_count = 0
            for k, v in ds['data_quality'].items():
                # the below DQ dimensions are given more weight in the calculation of the DQ score.
                if k in ['device_completeness', 'data_field_completeness', 'retention']:
                    score += (v * 2)
                    score_count += 2
                else:
                    score += v
                    score_count += 1
            if score > 0:
                score = score / score_count

            worksheet.write(y, 12, score, dq_score_0 if score == 0 else dq_score_1 if score < 2 else dq_score_2 if score < 3 else dq_score_3 if score < 4 else dq_score_4 if score < 5 else dq_score_5 if score < 6 else no_score)  # noqa
            y += 1

    worksheet.autofilter(2, 0, 2, 12)
    worksheet.freeze_panes(3, 0)
    try:
        workbook.close()
        print("File written:   " + excel_filename)
    except Exception as e:
        print('[!] Error while writing Excel file: %s' % str(e))


def _count_applicable_data_sources(technique, applicable_data_sources):
    """
    get the count of applicable data sources for the provided technique.
    This takes into account which data sources are applicable for a platform(s)
    :param technique: ATT&CK CTI technique object
    :param applicable_data_sources: a list of applicable ATT&CK data sources
    :return: a count of the applicable data sources for this technique
    """
    applicable_ds_count = 0
    for ds in technique['x_mitre_data_sources']:
        if ds in applicable_data_sources:
            applicable_ds_count += 1
    return applicable_ds_count


def _system_in_data_source(data_source, system):
    """
    Checks if the provided system is present within the provided YAML global data source object
    :param data_source: YAML data source object
    :param system: YAML system object
    :return: True if present otherwise False
    """
    for ds in data_source['data_source']:
        if system['applicable_to'].lower() in (app_to.lower() for app_to in ds['applicable_to']):
            return True
    return False


def _map_and_colorize_techniques(my_ds, systems, exceptions):
    """
    Determine the color of the techniques based on how many data sources are available per technique. Also, it will create
    much of the content for the Navigator layer.
    :param my_ds: the configured data sources
    :param systems: the systems YAML object from the data source file
    :param exceptions: the list of ATT&CK technique exception within the data source YAML file
    :return: a dictionary with techniques that can be used in the layer's output file
    """
    techniques = load_attack_data(DATA_TYPE_STIX_ALL_TECH)
    output_techniques = []

    for t in techniques:
        if 'x_mitre_data_sources' in t and get_attack_id(t) not in exceptions:
            ds_scores = []
            all_applicable_data_sources = set()
            system_available_data_sources = {}

            # calculate visibility score per system
            x = 0
            for system in systems:
                # the system is relevant for this technique due to a match in ATT&CK platform
                if len(set(system['platform']).intersection(set(t['x_mitre_platforms']))) > 0:
                    applicable_data_sources = get_applicable_data_sources_platform(system['platform'])
                    total_ds_count = _count_applicable_data_sources(t, applicable_data_sources)

                    if total_ds_count > 0:  # the system's platform has data source applicable to this technique
                        skey = ''.join(system['applicable_to']) + '_' + ''.join(system['platform'])
                        ds_count = 0
                        for ds in t['x_mitre_data_sources']:
                            if ds in applicable_data_sources:
                                all_applicable_data_sources.add(ds)
                                # the ATT&CK data source is applicable to this system and available
                                if ds in my_ds.keys() and _system_in_data_source(my_ds[ds], system):
                                    if ds_count == 0:
                                        system_available_data_sources[skey] = [ds]
                                    else:
                                        system_available_data_sources[skey].append(ds)
                                    ds_count += 1
                        if ds_count > 0:
                            ds_scores.append((float(ds_count) / float(total_ds_count)) * 100)
                        else:
                            ds_scores.append(0)  # the data source is not available for this system
                    else:
                        # the technique is applicable to this system (and thus its platform(s)),
                        # but none of the technique's listed data source are applicable its platform(s)
                        ds_scores.append(0)
                x += 1

            # check if not all ds_scores's values are 0. If not the case, we proceed in calculating the avg score
            # and populating the metadata.
            if not all(s == 0 for s in ds_scores):
                avg_ds_score = float(sum(ds_scores)) / float(len(ds_scores))

                color = COLOR_DS_25p if avg_ds_score <= 25 else COLOR_DS_50p if avg_ds_score <= 50 else COLOR_DS_75p \
                    if avg_ds_score <= 75 else COLOR_DS_99p if avg_ds_score <= 99 else COLOR_DS_100p

                d = dict()
                d['techniqueID'] = get_attack_id(t)
                d['color'] = color
                d['comment'] = ''
                d['enabled'] = True
                d['metadata'] = [{'name': 'Technique\'s ATT&CK data sources', 'value': ', '.join(all_applicable_data_sources)}]
                d['metadata'].append({'divider': True})

                scores_idx = 0
                divider = 0
                for system in systems:

                    # the system is relevant for this technique due to a match in ATT&CK platform
                    if len(set(system['platform']).intersection(set(t['x_mitre_platforms']))) > 0:
                        skey = ''.join(system['applicable_to']) + '_' + ''.join(system['platform'])
                        score = ds_scores[scores_idx]

                        if divider != 0:
                            d['metadata'].append({'divider': True})
                        divider += 1

                        d['metadata'].append({'name': 'Applicable to', 'value': system['applicable_to']})
                        app_data_sources = get_applicable_data_sources_technique(
                            t['x_mitre_data_sources'], get_applicable_data_sources_platform(system['platform']))
                        d['metadata'].append({'name': 'Applicable data sources', 'value': ', '.join(app_data_sources)})
                        if score > 0:
                            d['metadata'].append({'name': 'Available data sources', 'value': ', '.join(system_available_data_sources[skey])})
                        else:
                            d['metadata'].append({'name': 'Available data sources', 'value': ''})
                        d['metadata'].append({'name': 'Score', 'value': str(int(score)) + '%'})
                    scores_idx += 1

                d['metadata'] = make_layer_metadata_compliant(d['metadata'])
                output_techniques.append(d)

    determine_and_set_show_sub_techniques(output_techniques)

    return output_techniques


def _indent_comment(comment, indent):
    """
    Indent a multiline  general, visibility, detection comment by x spaces
    :param comment: The comment to indent
    :param indent: The number of spaces to use in the indent
    :return: indented comment or the original
    """
    if '\n' in comment:
        new_comment = comment.replace('\n', '\n' + ' ' * indent)
        return new_comment
    else:
        return comment


def _get_technique_yaml_obj(techniques, tech_id):
    """
    Get at technique YAML obj from the provided list of techniques YAML objects which as the provided technique ID
    :param techniques: list of technique YAML objects
    :param tech_id: ATT&CK ID
    :return: technique YAML obj
    """
    for tech in techniques:
        if tech['technique_id'] == tech_id:
            return tech


def update_technique_administration_file(file_data_sources, file_tech_admin):
    """
    Update the visibility scores in the provided technique administration file
    :param file_data_sources: file location of the data source admin. file
    :param file_tech_admin: file location of the tech. admin. file
    :return:
    """
    # first we generate the new visibility scores contained within a temporary tech. admin YAML 'file'
    new_visibility_scores = generate_technique_administration_file(file_data_sources, None, write_file=False)

    # we get the date to remove the single quotes at the end of the code
    today = new_visibility_scores['techniques'][0]['visibility']['score_logbook'][0]['date']

    # next we load the current visibility scores from the tech. admin file
    cur_visibility_scores, _, platform_tech_admin = load_techniques(file_tech_admin)

    # if the platform does not match between the data source and tech. admin file we return
    if set(new_visibility_scores['platform']) != set(platform_tech_admin):
        print('[!] The MITRE ATT&CK platform key-value pair in the data source administration and technique '
              'administration file do not match.\n    Visibility update canceled.')
        return

    # we did not return, so init
    _yaml = init_yaml()
    with open(file_tech_admin) as fd:
        yaml_file_tech_admin = _yaml.load(fd)

    # check if we have tech IDs for which we now have visibility, but which were not yet part of the tech. admin file
    cur_tech_ids = cur_visibility_scores.keys()
    new_tech_ids = list(map(lambda k: k['technique_id'], new_visibility_scores['techniques']))

    tech_ids_new = []
    for tid in new_tech_ids:
        if tid not in cur_tech_ids:
            tech_ids_new.append(tid)

    # Add the new tech. to the ruamel instance: 'yaml_file_tech_admin'
    are_scores_updated = False
    tech_new_print = []
    if len(tech_ids_new) > 0:

        # do we want fill in a comment for all updated visibility scores?
        comment = ''
        if ask_yes_no('\nDo you want to fill in the visibility comment for the updated scores?'):
            comment = input(' >>   Visibility comment for in the new \'score\' object: ')
            print('')

        # add new techniques and set the comment
        x = 0
        for new_tech in new_visibility_scores['techniques']:

            # set the comment for all new visibility scores
            # we will also be needing this later in the code to update the scores of already present techniques
            new_visibility_scores['techniques'][x]['visibility']['score_logbook'][0]['comment'] = comment

            if new_tech['technique_id'] in tech_ids_new:
                are_scores_updated = True
                yaml_file_tech_admin['techniques'].append(new_tech)
                tech_new_print.append(' - ' + new_tech['technique_id'] + '\n')
            x += 1

        print('The following new technique IDs are added to the technique administration file with a visibility '
              'score derived from the nr. of data sources:')
        print(''.join(tech_new_print))
    else:
        print(' - No new techniques, for which we now have visibility, have been added to the techniques administration file.')

    # determine how visibility scores have been assigned in the current YAML file (auto, manually or mixed)
    # also determine if we have any scores that can be updated
    manually_scored = False
    auto_scored = False
    mix_scores = False
    updated_vis_score_cnt = 0
    for cur_tech, cur_values in cur_visibility_scores.items():
        new_tech = _get_technique_yaml_obj(new_visibility_scores['techniques'], cur_tech)
        if new_tech:  # new_tech will be None if technique_id is part of the 'exception' list within the
            # data source administration file
            new_score = new_tech['visibility']['score_logbook'][0]['score']

            for cur_obj in cur_values['visibility']:
                old_score = get_latest_score(cur_obj)

                if get_latest_auto_generated(cur_obj) and old_score != new_score:
                    auto_scored = True
                    updated_vis_score_cnt += 1
                elif old_score != new_score:
                    manually_scored = True
                    updated_vis_score_cnt += 1

            if manually_scored and auto_scored:
                mix_scores = True

    # stop if none of the present visibility scores are eligible for an update
    if not mix_scores and not manually_scored and not auto_scored:
        print(' - None of the already present techniques has a visibility score that is eligible for an update.')
    else:
        print('\nA total of ' + str(updated_vis_score_cnt) + ' visibility scores are eligible for an update.\n')
        # ask how the score should be updated
        answer = 0
        if mix_scores:
            answer = ask_multiple_choice(V_UPDATE_Q_MIXED, [V_UPDATE_ANSWER_3, V_UPDATE_ANSWER_4,
                                                            V_UPDATE_ANSWER_1, V_UPDATE_ANSWER_2, V_UPDATE_ANSWER_CANCEL])
        elif manually_scored:
            answer = ask_multiple_choice(V_UPDATE_Q_ALL_MANUAL, [V_UPDATE_ANSWER_1, V_UPDATE_ANSWER_2, V_UPDATE_ANSWER_CANCEL])
        elif auto_scored:
            answer = ask_multiple_choice(V_UPDATE_Q_ALL_AUTO, [V_UPDATE_ANSWER_1, V_UPDATE_ANSWER_2, V_UPDATE_ANSWER_CANCEL])
        if answer == V_UPDATE_ANSWER_CANCEL:
            return

        # identify which visibility scores have changed and set the action to perform on the score
        # tech_update {tech_id: ..., {obj_idx: { action: 1|2|3, score_obj: {...} } } }
        tech_update = dict()
        for new_tech in new_visibility_scores['techniques']:
            tech_id = new_tech['technique_id']
            new_score_obj = new_tech['visibility']['score_logbook'][0]
            new_score = new_score_obj['score']

            if tech_id in cur_visibility_scores:
                old_visibility_objects = cur_visibility_scores[tech_id]['visibility']
                obj_idx = 0
                for old_vis_obj in old_visibility_objects:
                    old_score = get_latest_score(old_vis_obj)
                    auto_gen = get_latest_auto_generated(old_vis_obj)

                    # continue if score can be updated
                    if old_score != new_score:
                        if tech_id not in tech_update:
                            tech_update[tech_id] = dict()

                        if (answer == V_UPDATE_ANSWER_1) or (answer == V_UPDATE_ANSWER_3 and auto_gen):
                            tech_update[tech_id][obj_idx] = {'action': V_UPDATE_ACTION_AUTO, 'score_obj': new_score_obj}
                        elif answer == V_UPDATE_ANSWER_2:
                            tech_update[tech_id][obj_idx] = {'action': V_UPDATE_ACTION_DIFF, 'score_obj': new_score_obj}
                        elif answer == V_UPDATE_ANSWER_4:
                            if auto_gen:
                                tech_update[tech_id][obj_idx] = {'action': V_UPDATE_ACTION_AUTO, 'score_obj': new_score_obj}
                            else:
                                tech_update[tech_id][obj_idx] = {'action': V_UPDATE_ACTION_DIFF, 'score_obj': new_score_obj}
                    obj_idx += 1

        # perform the above set actions
        score_updates_handled = 0
        for old_tech in yaml_file_tech_admin['techniques']:
            tech_id = old_tech['technique_id']
            tech_name = old_tech['technique_name']
            obj_idx = 0
            if tech_id in tech_update:
                if isinstance(old_tech['visibility'], list):
                    old_vis_obj = old_tech['visibility']
                else:
                    old_vis_obj = [old_tech['visibility']]

                while obj_idx <= len(tech_update[tech_id]):
                    # continue if an action has been set for this visibility object
                    if obj_idx in tech_update[tech_id]:
                        update_action = tech_update[tech_id][obj_idx]['action']
                        new_score_obj = tech_update[tech_id][obj_idx]['score_obj']

                        if update_action == V_UPDATE_ACTION_AUTO:
                            are_scores_updated = True
                            old_vis_obj[obj_idx]['score_logbook'].insert(0, new_score_obj)
                            print(' - Updated a score in technique ID: ' + tech_id +
                                  '   (applicable to: ' + ', '.join(old_vis_obj[obj_idx]['applicable_to']) + ')')
                        elif update_action == V_UPDATE_ACTION_DIFF:
                            print('-' * 80)
                            tmp_txt = '[updates remaining: ' + str(updated_vis_score_cnt - score_updates_handled) + ']'
                            print(' ' * (80 - len(tmp_txt)) + tmp_txt)
                            print('')
                            print('Visibility object:')
                            print(' - ATT&CK ID/name      ' + tech_id + ' / ' + tech_name)
                            print(' - Applicable to:      ' + ', '.join(old_vis_obj[obj_idx]['applicable_to']))
                            print(' - Technique  comment: ' + _indent_comment(old_vis_obj[obj_idx]['comment'], 23))
                            print('')
                            print('OLD score object:')
                            old_score_date = get_latest_date(old_vis_obj[obj_idx])
                            old_score_date = old_score_date.strftime('%Y-%m-%d') if old_score_date is not None else ''
                            print(' - Date:               ' + old_score_date)
                            print(' - Score:              ' + str(get_latest_score(old_vis_obj[obj_idx])))
                            print(' - Visibility comment: ' + _indent_comment(get_latest_comment(old_vis_obj[obj_idx]), 23))
                            print(' - Auto generated:     ' + str(get_latest_score_obj(old_vis_obj[obj_idx]).get('auto_generated', 'False')))
                            print('NEW score object:')
                            print(' - Date:               ' + str(new_score_obj['date']))
                            print(' - Score:              ' + str(new_score_obj['score']))
                            print(' - Visibility comment: ' + _indent_comment(new_score_obj['comment'], 23))
                            print(' - Auto generated:     True')
                            print('')
                            if ask_yes_no('Update the score?'):
                                are_scores_updated = True
                                old_vis_obj[obj_idx]['score_logbook'].insert(0, new_score_obj)
                                print(' - Updated a score in technique ID: ' + tech_id +
                                      '   (applicable to: ' + ', '.join(old_vis_obj[obj_idx]['applicable_to']) + ')')

                        score_updates_handled += 1

                    obj_idx += 1

    # create backup of the current tech. admin YAML file
    if are_scores_updated:
        print('')
        backup_file(file_tech_admin)

        yaml_file_tech_admin = fix_date_and_remove_null(yaml_file_tech_admin, today, input_type='ruamel')

        with open(file_tech_admin, 'w') as fd:
            fd.writelines(yaml_file_tech_admin)
        print('File written:   ' + file_tech_admin)
    else:
        print('No visibility scores have been updated.')

# pylint: disable=redefined-outer-name


def generate_technique_administration_file(filename, output_filename, write_file=True, all_techniques=False):
    """
    Generate a technique administration file based on the data source administration YAML file
    :param filename: the filename of the YAML file containing the data sources administration
    :param output_filename: the output filename defined by the user
    :param write_file: by default the file is written to disk
    :param all_techniques: include all ATT&CK techniques in the generated YAML file that are applicable to the
    platform(s) specified in the data source YAML file
    :return:
    """
    my_data_sources, name, platform, exceptions = load_data_sources(filename)

    techniques = load_attack_data(DATA_TYPE_STIX_ALL_TECH_ENTERPRISE)
    applicable_data_sources = get_applicable_data_sources_platform(platform)

    yaml_file = dict()
    yaml_file['version'] = FILE_TYPE_TECHNIQUE_ADMINISTRATION_VERSION
    yaml_file['file_type'] = FILE_TYPE_TECHNIQUE_ADMINISTRATION
    yaml_file['name'] = name
    yaml_file['platform'] = platform
    yaml_file['techniques'] = []
    today = dt.now()

    # Score visibility based on the number of available data sources and the exceptions
    for t in techniques:
        platforms = t.get('x_mitre_platforms', None)
        if len(set(platforms).intersection(set(platform))) > 0:
            # not every technique has data source listed
            if 'x_mitre_data_sources' in t:
                total_ds_count = _count_applicable_data_sources(t, applicable_data_sources)
                ds_count = 0
                for ds in t['x_mitre_data_sources']:
                    if ds in my_data_sources.keys() and ds in applicable_data_sources:
                        ds_count += 1
                if total_ds_count > 0:
                    result = (float(ds_count) / float(total_ds_count)) * 100

                    score = 0 if result == 0 else 1 if result <= 49 else 2 if result <= 74 else 3 if result <= 99 else 4
                else:
                    score = 0

                # Do not add technique if score == 0 or part of the exception list
                techniques_upper = list(map(lambda x: x.upper(), exceptions))
                tech_id = get_attack_id(t)
                if (score > 0 or all_techniques) and tech_id not in techniques_upper:
                    tech = deepcopy(YAML_OBJ_TECHNIQUE)
                    tech['technique_id'] = tech_id
                    tech['technique_name'] = t['name']
                    tech['visibility']['score_logbook'][0]['score'] = score
                    tech['visibility']['score_logbook'][0]['date'] = today
                    yaml_file['techniques'].append(tech)

    yaml_file['techniques'] = sorted(yaml_file['techniques'], key=lambda k: k['technique_id'])

    if write_file:
        # remove the single quotes around the date key-value pair
        _yaml = init_yaml()
        file = StringIO()

        # create the file lines by writing it to memory
        _yaml.dump(yaml_file, file)
        file.seek(0)
        file_lines = file.readlines()

        # remove the single quotes from the date
        yaml_file_lines = fix_date_and_remove_null(file_lines, today, input_type='list')

        if not output_filename:
            output_filename = 'techniques-administration-' + normalize_name_to_filename(name + '-' + platform_to_name(platform))
        elif output_filename.endswith('.yaml'):
            output_filename = output_filename.replace('.yaml', '')
        output_filename = get_non_existing_filename('output/' + output_filename, 'yaml')
        with open(output_filename, 'w') as f:
            f.writelines(yaml_file_lines)
        print("File written:   " + output_filename)
    else:
        return yaml_file
