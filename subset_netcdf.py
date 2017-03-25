import subprocess
import shutil
import os
import logging
import datetime
import platform
from subsetting_lib import subset_grid_file, subset_comid_file, merge_netcdf

logger = logging.getLogger('subset_netcdf')


def render_cdl_file(content_list=[], file_path=None):
    for item in content_list:
        replace_text_in_file(search_text=item[0], replace_text=item[1], file_path=file_path)


def replace_text_in_file(search_text=None, replace_text=None, file_path=None):
    # subprocess.call(['sed', '-i', 's/{0}/{1}/g'.format(search_text, replace_text), file_path])
    if "windows" in platform.system().lower():
        sed_cmd = ['.\\dependencies\\sed_win\\sed.exe', "-i", "s/{0}/{1}/g".format(search_text, replace_text), file_path]
    elif "linux" in platform.system().lower():
        sed_cmd = ['sed', '-i', 's/{0}/{1}/g'.format(search_text, replace_text), file_path]
    else:
        raise Exception("Unsupported OS")
    proc = subprocess.Popen(sed_cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            )
    proc.wait()
    stdout, stderr = proc.communicate()
    if stdout:
        logger.error(stdout)
        raise Exception(" replace_text_in_file() error @ {0}".format(file_path))
    if stderr:
        logger.error(stderr)
        raise Exception(" replace_text_in_file() error @ {0}".format(file_path))


def create_nc_from_cdf(cdl_file=None, out_file=None, remove_cdl=True):
    # -7: netcdf-4 classic model
    # subprocess.call(['ncgen', '-7', '-o', out_file, cdl_file])
    ncgen_cmd = ['ncgen', '-7', '-o', out_file, cdl_file]
    proc = subprocess.Popen(ncgen_cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            )
    proc.wait()
    stdout, stderr = proc.communicate()
    if stdout:
        logger.error(stdout)
        raise Exception(" create_nc_from_cdf() error @ {0}".format(cdl_file))
    if stderr:
        logger.error(stderr)
        raise Exception(" create_nc_from_cdf() error @ {0}".format(cdl_file))

    if remove_cdl:
        os.remove(cdl_file)


def subset_nwm_netcdf(job_id=None,
                      grid=None,
                      comid_list=None,
                      simulation_date=None,
                      data_type=None,
                      model_type=None,
                      file_type=None,
                      input_folder_path=None,
                      output_folder_path=None,
                      template_folder_path=None,
                      template_version="v1.1",
                      write_file_list=None,
                      use_merge_template=False,
                      cleanup=False,
                      use_chunked_template=True):

    if job_id is None:
        job_id = "NO_JOB_ID"
    output_folder_path = os.path.join(output_folder_path, job_id)
    data_type = data_type.lower()
    model_type = model_type.lower() if model_type else None
    file_type = file_type.lower() if file_type else None
    template_version = template_version.lower()

    dim_x_len = grid['maxX'] - grid['minX'] + 1
    dim_y_len = grid['maxY'] - grid['minY'] + 1

    # index_x_old = index_x_new + index_offset_x
    index_offset_x = grid["minX"]
    # index_y_old = index_y_new + index_offset_y
    index_offset_y = grid["minY"]

    var_list = []
    if data_type == "forcing":
        if model_type == "analysis_assim":
            cdl_template_filename = "nwm.tHHz.analysis_assim.forcing.tm00.conus.cdl_template"
            var_list.append(["HH", range(24)])  # 00, 01, ... 23
        elif model_type == "short_range":
            cdl_template_filename = "nwm.tHHz.short_range.forcing.fXXX.conus.cdl_template"
            var_list.append(["HH", range(24)])  # 00, 01, ... 23
            var_list.append(["XXX", range(1, 19)])  # 001, 0002 ... 018
        elif model_type == "medium_range":
            cdl_template_filename = "nwm.tHHz.medium_range.forcing.fXXX.conus.cdl_template"
            var_list.append(["HH", range(0, 19, 6)])  # 00, 06, 12, 18
            var_list.append(["XXX", range(1, 241)])  # 001, 002, .... 240
        elif model_type == "long_range":
            raise Exception("Long-range forecast has no dedicated forcing files.")

    elif data_type == "forecast":
        if model_type == "analysis_assim":
            var_list.append(["HH", range(24)])  # 00, 01, 02...23

            if file_type == "channel":
                cdl_template_filename = "nwm.tHHz.analysis_assim.channel_rt.tm00.conus.cdl_template"
            elif file_type == "land":
                cdl_template_filename = "nwm.tHHz.analysis_assim.land.tm00.conus.cdl_template"
            elif file_type == "reservoir":
                cdl_template_filename = "nwm.tHHz.analysis_assim.reservoir.tm00.conus.cdl_template"
            elif file_type == "terrain":
                raise NotImplementedError()

        elif model_type == "short_range":
            var_list.append(["HH", range(24)])  # 00, 01, ... 23
            var_list.append(["XXX", range(1, 19)])  # 001, 002 ... 18

            if file_type == "channel":
                cdl_template_filename = "nwm.tHHz.short_range.channel_rt.fXXX.conus.cdl_template"
            elif file_type == "land":
                cdl_template_filename = "nwm.tHHz.short_range.land.fXXX.conus.cdl_template"
            elif file_type == "reservoir":
                cdl_template_filename = "nwm.tHHz.short_range.reservoir.fXXX.conus.cdl_template"
            elif file_type == "terrain":
                raise NotImplementedError()

        elif model_type == "medium_range":
            var_list.append(["HH", range(0, 19, 6)])  # 00, 06, ... 18
            var_list.append(["XXX", range(3, 241, 3)])  # 003, 006, 009, ... 240

            if file_type == "channel":
                cdl_template_filename = "nwm.tHHz.medium_range.channel_rt.fXXX.conus.cdl_template"
            elif file_type == "land":
                cdl_template_filename = "nwm.tHHz.medium_range.land.fXXX.conus.cdl_template"
            elif file_type == "reservoir":
                cdl_template_filename = "nwm.tHHz.medium_range.reservoir.fXXX.conus.cdl_template"
            elif file_type == "terrain":
                raise NotImplementedError()

        elif "long_range_mem" in model_type:
            mem_id = int(model_type[-1])
            if mem_id in [1, 2, 3, 4]:
                var_list.append(["M", [mem_id]])  # 1, 2, 3, 4
                var_list.append(["HH", range(0, 19, 6)])  # 00, 06, 12, 18

                if file_type == "channel":
                    var_list.append(["XXX", range(6, 721, 6)])  # 006, 012, 018, ... 720
                    cdl_template_filename = "nwm.tHHz.long_range.channel_rt_M.fXXX.conus.cdl_template"
                elif file_type == "land":
                    var_list.append(["XXX", range(24, 721, 24)])  # 024, 048, ... 720
                    cdl_template_filename = "nwm.tHHz.long_range.land_M.fXXX.conus.cdl_template"
                elif file_type == "reservoir":
                    var_list.append(["XXX", range(6, 721, 6)])  # 006, 012, 018, ... 720
                    cdl_template_filename = "nwm.tHHz.long_range.reservoir_M.fXXX.conus.cdl_template"
                elif file_type == "terrain":
                    raise NotImplementedError("terrain")
            else:
                raise Exception("Invalid long_rang model type @: {0}".format(model_type))

    else:
        raise Exception("invalid data_type: {0}".format(data_type))

    if use_merge_template:
        cdl_template_filename += "_merge"

    if use_chunked_template:
        cdl_template_filename += "_chunked"

    if "long_range_mem" in model_type:
        # long_range uses same templates for all mem1-mem4
        cdl_template_file_path = os.path.join(template_folder_path, template_version,
                                     data_type, "long_range", cdl_template_filename)
    else:
        cdl_template_file_path = os.path.join(template_folder_path, template_version,
                                     data_type, model_type, cdl_template_filename)

    if not os.path.isfile(cdl_template_file_path):
        raise Exception("template file missing @: {0}".format(cdl_template_file_path))

    cdl_filename = cdl_template_filename[0:cdl_template_filename.rfind("_template")]
    nc_template_file_name = cdl_filename.replace(".cdl", ".nc")
    out_nc_folder_template_path = os.path.join(output_folder_path, "nc_template")
    nc_template_file_path = os.path.join(out_nc_folder_template_path, nc_template_file_name)

    # # render a template nc file and put it under output folder
    # if not os.path.isfile(nc_template_file_path):
    #     if not os.path.exists(out_nc_folder_template_path):
    #         os.makedirs(out_nc_folder_template_path)
    #     cdl_file_path = os.path.join(out_nc_folder_template_path, cdl_filename)
    #     shutil.copyfile(cdl_template_file_path, cdl_file_path)
    #
    #     content_list = []
    #     if data_type == "forecast" and file_type in ["channel", "reservoir"]:
    #         if file_type == "channel" and len(comid_list) == 0:
    #             return
    #         if file_type == "reservoir" and len(comid_list) == 0:
    #             return
    #         content_list.append(["{%feature_id%}", str(len(comid_list))])
    #     elif data_type == "forcing" or \
    #             (data_type == "forecast" and file_type in ["land"]):
    #         content_list.append(["{%x%}", str(dim_x_len)])
    #         content_list.append(["{%y%}", str(dim_y_len)])
    #
    #     content_list.append(["{%filename%}", nc_template_file_name])
    #     content_list.append(["{%model_initialization_time%}", "2030-01-01_00:00:00"])
    #     content_list.append(["{%model_output_valid_time%}", "2030-01-01_00:00:00"])
    #
    #     render_cdl_file(content_list=content_list, file_path=cdl_file_path)
    #     create_nc_from_cdf(cdl_file=cdl_file_path, out_file=nc_template_file_path)

    nc_file_name = nc_template_file_name
    nc_filename_list = [nc_file_name]
    for var in var_list:
        var_name = var[0]
        var_range = var[1]
        nc_filename_list_new = []
        for nc in nc_filename_list:
            for var_value in var_range:
                var_value_str = str(var_value).zfill(len(var_name))
                nc_new = nc
                nc_new = nc_new.replace(var_name, var_value_str)
                nc_filename_list_new.append(nc_new)
        nc_filename_list = nc_filename_list_new

    # write wget download list file
    if type(write_file_list) is dict:
        url_base = write_file_list["url_base"] + "nwm.$simulation_date/"
        save_to_path_base = os.path.join(write_file_list["save_to_path_base"],
                                         "nwm.simulation_date")
        # -nc: do not download file if it already exists on disk
        wget_cmd_template = "wget -nc -P {save_to_folder_path} {url}"
        write_file_list_path = "./file_list_{0}.txt".format(job_id)
        with open(write_file_list_path, "a+") as f:
            if os.path.getsize(write_file_list_path) == 0:
                f.write("simulation_date={simulation_date}\n".format(simulation_date=simulation_date))
            for nc_filename in nc_filename_list:
                save_to_folder_path = os.path.join(save_to_path_base, model_type)
                url = url_base + model_type + "/" + nc_filename
                if data_type == "forcing":
                    save_to_folder_path = os.path.join(save_to_path_base, data_type + "_" + model_type)
                    url = url_base + data_type + "_" + model_type + "/" + nc_filename
                save_to_folder_path = save_to_folder_path.replace("simulation_date", "$simulation_date")
                wget_cmd = wget_cmd_template.format(save_to_folder_path=save_to_folder_path, url=url)
                f.write(wget_cmd + "\n")
        print("file list written to {0}".format(write_file_list_path))
        return

    simulation_date = "nwm." + simulation_date
    out_nc_folder_path = os.path.join(output_folder_path, simulation_date, model_type)
    in_nc_folder_path = os.path.join(input_folder_path, simulation_date, model_type)
    if data_type == "forcing":
        out_nc_folder_path = os.path.join(output_folder_path, simulation_date, data_type + "_" + model_type)
        in_nc_folder_path = os.path.join(input_folder_path, simulation_date, data_type + "_" + model_type)

    if not os.path.exists(out_nc_folder_path):
        os.makedirs(out_nc_folder_path)

    comid_list_dict = {"channel": None, "reservoir": None}
    direct_read = None
    comid_list_dict[file_type] = comid_list
    index_list_dict = {"channel": None, "reservoir": None}
    for nc_filename in nc_filename_list:
        out_nc_file = os.path.join(out_nc_folder_path, nc_filename)
        in_nc_file = os.path.join(in_nc_folder_path, nc_filename)
        if not os.path.isfile(in_nc_file):
            logger.warning("Original netcdf missing @: {0}".format(in_nc_file))
            # skip this netcdf as its original file is missing
            continue

        if os.path.isfile(out_nc_file):
            logger.debug("Overwriting existing nc file @: {0}".format(out_nc_file))

        # render a template nc file and put it under output folder
        if not os.path.isfile(nc_template_file_path):
            if not os.path.exists(out_nc_folder_template_path):
                os.makedirs(out_nc_folder_template_path)
            cdl_file_path = os.path.join(out_nc_folder_template_path, cdl_filename)
            shutil.copyfile(cdl_template_file_path, cdl_file_path)

            content_list = []
            if data_type == "forecast" and file_type in ["channel", "reservoir"]:
                if file_type == "channel" and len(comid_list) == 0:
                    return
                if file_type == "reservoir" and len(comid_list) == 0:
                    return
                content_list.append(["{%feature_id%}", str(len(comid_list))])
            elif data_type == "forcing" or \
                    (data_type == "forecast" and file_type in ["land"]):
                content_list.append(["{%x%}", str(dim_x_len)])
                content_list.append(["{%y%}", str(dim_y_len)])

            content_list.append(["{%filename%}", nc_template_file_name])
            content_list.append(["{%model_initialization_time%}", "2030-01-01_00:00:00"])
            content_list.append(["{%model_output_valid_time%}", "2030-01-01_00:00:00"])

            render_cdl_file(content_list=content_list, file_path=cdl_file_path)
            create_nc_from_cdf(cdl_file=cdl_file_path, out_file=nc_template_file_path)

        shutil.copyfile(nc_template_file_path, out_nc_file)

        if data_type == "forcing" or \
           data_type == "forecast" and file_type == "land":

            subset_grid_file(in_nc_file=in_nc_file,
                             out_nc_file=out_nc_file,
                             grid_dict=grid)

        elif data_type == "forecast" and (file_type == "channel" or file_type == "reservoir"):

            comid_list_dict[file_type], index_list_dict[file_type], direct_read = \
                subset_comid_file(in_nc_file=in_nc_file,
                                  out_nc_file=out_nc_file,
                                  comid_list=comid_list_dict[file_type],
                                  index_list=index_list_dict[file_type],
                                  reuse_comid_and_index=True,
                                  direct_read=direct_read)
    if cleanup:
        # remove nc_template folder
        shutil.rmtree(out_nc_folder_template_path)


def start_subset(job_id=None, netcdf_folder_path=None, output_folder_path=None,
                 template_folder_path=None, simulation_date_list=None, data_type_list=None,
                 model_type_list=None, file_type_list=None, grid_dict=None, stream_comid_list=None,
                 reservoir_comid_list=None,
                 merge_netcdfs=True, cleanup=True, write_file_list=None, template_version="v1.1",
                 use_chunked_template=True):

    logger.info("---------------Subsetting {0}----------------".format(job_id))
    start_dt = datetime.datetime.now()
    logger.info(start_dt)

    logger.info("job_id={0}".format(str(job_id)))
    logger.info("netcdf_folder_path={0}".format(str(netcdf_folder_path)))
    logger.info("output_folder_path={0}".format(str(output_folder_path)))
    logger.info("template_folder_path={0}".format(str(template_folder_path)))
    logger.info("simulation_date_list={0}".format(str(simulation_date_list)))
    logger.info("data_type_list={0}".format(str(data_type_list)))
    logger.info("model_type_list={0}".format(str(model_type_list)))
    logger.info("file_type_list={0}".format(str(file_type_list)))
    logger.info("grid_dict={0}".format(str(grid_dict)))
    logger.info("stream_comid_list={0}".format(str(stream_comid_list)))
    logger.info("reservoir_comid_list={0}".format(str(reservoir_comid_list)))
    logger.info("merge_netcdfs={0}".format(str(merge_netcdfs)))
    logger.info("cleanup={0}".format(str(cleanup)))
    logger.info("write_file_list={0}".format(str(write_file_list)))
    logger.info("template_version={0}".format(str(template_version)))

    if "long_range" in model_type_list:
        model_type_list.remove("long_range")
        for i in range(1, 5):
            model_type_list.append("long_range_mem{0}".format(str(i)))

    subset_work_dict = {'simulation_date': simulation_date_list,
                        'date_type': data_type_list,
                        'model_type': model_type_list,
                        'file_type':  file_type_list
                        }

    for simulation_date in subset_work_dict["simulation_date"]:
        logger.info("-------------Subsetting {0}--------------------".format(simulation_date))
        for data_type in subset_work_dict["date_type"]:
            for model_type in subset_work_dict["model_type"]:
                data_type_list_copy = subset_work_dict['file_type']
                if data_type == "forcing":
                    data_type_list_copy = [None]
                    if "long_range" in model_type:
                        # long_range has no dedicated forcing files
                        continue
                for file_type in data_type_list_copy:
                    try:
                        comid_list = stream_comid_list
                        if 'reservoir' == file_type:
                            comid_list = reservoir_comid_list
                        log_str = "Working on: {simulation_date}-{data_type}-{model_type}-{file_type}".\
                            format(simulation_date=simulation_date, data_type=data_type,
                                   model_type=model_type, file_type=file_type)
                        logger.info(log_str)
                        sim_start_dt = datetime.datetime.now()
                        logger.debug(sim_start_dt)
                        subset_nwm_netcdf(job_id=job_id,
                                          grid=grid_dict,
                                          comid_list=comid_list,
                                          simulation_date=simulation_date,
                                          data_type=data_type,
                                          model_type=model_type,
                                          file_type=file_type,
                                          input_folder_path=netcdf_folder_path,
                                          output_folder_path=output_folder_path,
                                          template_folder_path=template_folder_path,
                                          template_version=template_version,
                                          write_file_list=write_file_list,
                                          use_merge_template=merge_netcdfs,
                                          cleanup=cleanup,
                                          use_chunked_template=use_chunked_template)
                        sim_end_dt = datetime.datetime.now()
                        logger.debug(sim_end_dt)
                        sim_elapsed = sim_end_dt - sim_start_dt
                        logger.info("Done in {0}; Subsetting Elapsed: {1}".format(sim_elapsed, sim_end_dt - start_dt))
                    except Exception as ex:
                        logger.error(str(type(ex)) + ex.message)

    end_dt = datetime.datetime.now()
    logger.debug(end_dt)
    elapse_dt = end_dt - start_dt
    logger.info(elapse_dt)
    logger.info("---------------------Subsetting Done-----------------------------")

    if merge_netcdfs:
        logger.info("---------------------Start Merging-----------------------------")
        merge_start_dt = datetime.datetime.now()
        logger.debug(merge_start_dt)
        for simulation_date in subset_work_dict["simulation_date"]:
            logger.info("Merging {0}-------------------------------".format(simulation_date))
            merge_netcdf(input_base_path=os.path.join(output_folder_path, job_id, "nwm.{0}".format(simulation_date)),
                         cleanup=cleanup)
        merge_end_dt = datetime.datetime.now()
        logger.debug(merge_end_dt)
        merge_elapse_dt = merge_end_dt - merge_start_dt
        logger.info(merge_elapse_dt)
        logger.info("---------------------Merge Done-----------------------------")
    pass

# if __name__ == "__main__":
#
#     netcdf_folder_path = "/media/sf_Shared_Folder/new_data"
#     output_folder_path = "./temp"
#     template_folder_path = "./netcdf_templates"
#     template_version = "v1.1"
#
#     merge_netcdfs = True
#     cleanup = True
#
#     simulation_date_list = ["20170319"]
#
#     #data_type_list = ['forcing', "forecast"]
#     data_type_list = ['forecast']
#
#     #model_type_list = ['analysis_assim', 'short_range', 'medium_range', 'long_range']
#     model_type_list = ['analysis_assim']
#
#     #file_type_list = ['channel', 'reservoir', 'land']
#     file_type_list = ['channel', 'reservoir']
#
#     write_file_list = None
#     # write_file_list = {"url_base": "http://para.nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/para/",
#     #                     "save_to_path_base": "/projects/water/nwm/new_data/pub/data/nccf/com/nwm/para/"}
#     # write_file_list = {"url_base": "http://para.nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/para/",
#     #                    "save_to_path_base": "/cygdrive/f/nwm_new_data/"}
#
#     grid_dict = {}
#     grid_dict["minX"] = 837
#     grid_dict["maxX"] = 1328
#     grid_dict["minY"] = 1673
#     grid_dict["maxY"] = 2279
#
#     # stream_comid_list = [16770078, 16770050, 16770058, 16770108, 16768504, 16767598, 16768488, 16768798, 16768806, 16767298, 16768802, 16768812, 16768814, 16768818, 16768816, 16770526, 16770068, 16770066, 16770116, 16770138, 16770904, 16770090, 16770094, 16770556, 16770546, 16770686, 16770908, 16770912, 16770916, 16770528, 16768502, 16770530, 16770538, 27571242, 16768690, 16768484, 16768492, 16766972, 16766988, 16766984, 16767028, 16768508, 16768516, 16768500, 16768736, 16767150, 16768514, 16768732, 16768696, 16767324, 16768734, 16767618, 16770518, 16782644, 16767574, 16767602, 16768820, 16767530, 16767606, 16767620, 16770004, 16768752, 16767576, 16767600, 16768750, 16768748, 16770638, 16770026, 16770070, 16770052, 16770540, 16770088, 16770652, 16770076, 16770542, 16770702, 16770148, 16770694, 16770150, 16770692, 16770178, 16770708, 16770164, 16770688, 16770680, 16770130, 16770668, 16770548, 16770170, 16770144, 16770146, 16770726, 16770568, 16770734, 16770580, 16768740, 16768738, 16770132, 16770552, 16770102, 16770660, 16767036, 16770044, 16770082, 16770662, 16770100, 16770152, 16767584, 16767582, 16770676, 16770666, 16770664, 16782660, 16768742, 16768746, 16768744, 16770650, 16771168, 16771170, 16771164, 16771166, 16770654, 16770658, 16770656, 16770696, 16770698, 16770700, 16768754, 27571234, 27571236, 27571238, 27571232, 16766916]
#     stream_comid_list = [20230169, 20230175, 948091305, 948091306, 948091304, 20228951, 20229053, 948090444, 20229025,
#                   20228981, 20230241,
#                   20230215, 20230209, 20230237, 20230249, 20228961, 20229199, 20229153, 20229171, 20229173, 20229223,
#                   20229193,
#                   20229015, 20229489, 20230003, 20229229, 20229231, 20230001, 20229965, 20230009, 20230027, 20230055,
#                   20229227,
#                   948090657, 20229069, 20229131, 20229147, 20230089, 20230101, 20230075, 20230049, 20230047, 20229297,
#                   20230015,
#                   20230091, 20230123, 20230007, 20229067, 948090643, 20229115, 20229139, 20229161, 20230267, 20229021,
#                   20230227,
#                   20230221, 20230225, 20230223, 20230211, 20230205, 20228979, 20228963, 20229501, 20229075, 20229137,
#                   20229105,
#                   20229113, 20229163, 20229503, 20229003, 20229085, 20229221, 20229305, 20229977, 20229203, 20229205,
#                   20229217,
#                   20229237, 20229241, 20229247, 20229289, 20229299, 20230391, 20229979, 20229303, 20229301, 20229245,
#                   20229215,
#                   948090654, 20229043, 20229045, 20229051, 20229057, 20229047, 948090489, 20229081, 20229049, 20229041,
#                   20230121,
#                   20230105, 20230103, 20230077, 20230081, 20230093, 20230079, 20230083, 20230013, 20230045, 20229035,
#                   20229039,
#                   20229077, 948090644, 948090655, 948090656, 948091307, 948091308, 948091309, 20230283, 948090645,
#                   948090646,
#                   948090647, 20230033, 20229261, 20230151, 20230171, 20230197, 20230233, 20230253, 20229719, 20230133,
#                   20230247,
#                   20228977, 20229669, 20229673, 20229677, 20229881, 20229691, 20229703, 20228921, 20229491, 20230411,
#                   20229063,
#                   20229179, 20229111, 20229011, 20229149, 20229211, 20228999, 20228987, 20229185, 20229181, 20230109,
#                   20230375,
#                   948090662, 20230381, 20230149, 20230157, 20230179, 20230259, 20230275, 20230281, 20229685, 20230505,
#                   20230503,
#                   20229747, 20230585, 20230875, 20230871, 20230591, 20230877, 20230879, 20230589, 20230565, 20230583,
#                   20230597,
#                   20230595, 20230571, 20230525, 20230537, 20230465, 20229745, 20230471, 20229675, 20229687, 20229699,
#                   20229739,
#                   20229717, 20229751, 20229715, 20229705, 20229883, 20229091, 20229023, 20229083, 20228957, 20230145,
#                   20230153,
#                   20230373, 20230115, 20230117, 20230185, 20230193, 20230203, 948090663, 20230383, 20230159, 20230191,
#                   20229885,
#                   20229755, 20230479, 20230881, 20229749, 20230457, 20230887, 20230853, 20230495, 20230507, 20230541,
#                   20230567,
#                   20230549, 20230573, 20230575, 20230581, 20230509, 20230515, 20230543, 20230545, 20230555, 20230557,
#                   20230579,
#                   20230559, 20230563, 20230519, 20230523, 20230527, 20230529, 20230551, 20230547, 20230521, 20230491,
#                   20230467,
#                   20229681, 20229689, 20229697, 20229711, 20229701, 20228985, 20230213, 20230263, 20230199, 20230229,
#                   20230201,
#                   20230187, 20230161, 20230163, 20230219, 20230859, 20230539, 20230873, 20230517, 20230857, 20229679,
#                   20229743,
#                   20229693, 20230483, 20230499, 20230473, 20230469, 20230051, 20229273, 20229279, 20230129, 20229275,
#                   20229277,
#                   20230043, 20229263, 20229265, 20230855, 20230531, 20230533, 20230273, 20230235, 20230257, 20230231,
#                   948090660,
#                   948090661, 948090458, 948090459, 20230217, 20230189, 948090898, 948090659, 948090899, 20230085,
#                   20230513, 20230511,
#                   20230107, 20230535, 20228991, 948090470, 20228941, 20229695, 20228965, 20229065, 20229733, 948090471,
#                   20229759,
#                   20229757, 20230459, 20230463, 20230165, 948090456, 20230135, 20230071, 20230073, 20230137, 20230125,
#                   20230127,
#                   20230119, 20230111, 20229985, 20229973, 20230397, 20229983, 20229971, 20230113, 20229283, 20230005,
#                   20230401,
#                   948090896, 948090897, 20229753, 20235757, 20229255, 20230883, 20230487, 20230885, 20230561, 20230399,
#                   20229257,
#                   20229963, 20229967, 20229565, 20229567, 20229569, 20230403, 20230405, 20230407, 20230409, 948090230,
#                   948090457,
#                   948091116, 20230587, 20230593, 20230553, 20230569, 20230865, 20230861, 20230869, 20230577, 20229741,
#                   20230475,
#                   20229653, 20229657, 20228881, 20229665, 20229889, 20229891, 20229893, 20229897, 20229909, 20229899,
#                   20229903,
#                   20229901, 20229895, 20229905, 20229907, 20229667, 20228401, 20229619, 20229659, 20229637, 20229635,
#                   20229633,
#                   20229661, 20229645, 20229641, 20229643, 20229875, 20229663, 20229877, 20229873, 20229671, 20229631,
#                   20229651,
#                   20229647, 20228663, 20228403, 20228631, 20229655, 20229639, 20229911, 20229879, 20228875, 20228719,
#                   20228661,
#                   20229587, 20228717, 20229649, 20228819, 20228627, 20229617, 20229625, 20229629, 20229623, 20229399,
#                   20229871,
#                   20229621, 20228425, 20229397, 20228423, 20229627, 20228297, 20228273, 24912091, 24912093, 24912095,
#                   24912097,
#                   24912099, 24912101, 24912103, 163864534, 163864535, 24912107, 24912109, 24912111, 24912113, 24912115,
#                   24912117,
#                   24912119, 24912121, 24912123, 24912125, 24912127, 24912129, 20247494, 948090639, 20229363, 20226241,
#                   20227633,
#                   20229591, 20227781, 948090327, 20227789, 20227639, 20227671, 20227677, 20227713, 20227729, 20227735,
#                   20227751,
#                   20227799, 20227809, 20227821, 20227843, 20229589, 20229385, 20227999, 20228025, 20228075, 20228087,
#                   20228137,
#                   20229425, 20228225, 20228235, 20228257, 20228259, 20228277, 20228279, 948090650, 948090651, 20228435,
#                   20228639,
#                   20228645, 20228649, 20228655, 20228677, 20228715, 20228751, 948090640, 948090637, 948090638, 20228745,
#                   20228753,
#                   20228767, 20228769, 20225943, 20228703, 20228253, 20227835, 20225707, 20225709, 20225711, 20226483,
#                   20225741,
#                   20225745, 20225759, 20225771, 20225797, 20225805, 20225821, 20225825, 20225837, 20226503, 20225849,
#                   20225855,
#                   20225883, 20228887, 20228911, 20228755, 20229467, 20228389, 20228367, 20227923, 20227927, 20227931,
#                   20227929,
#                   20229383, 20227833, 20227837, 20226187, 20226193, 20228085, 20228105, 20224359, 20224347, 20224627,
#                   20224379,
#                   20224377, 20226471, 20224417, 20225635, 20224635, 20224409, 20224633, 20224637, 20224415, 20225921,
#                   20225879,
#                   20225877, 20224375, 20224625, 20226467, 20225621, 20226469, 20225625, 20224413, 20225623, 20225615,
#                   20224411,
#                   20224641, 20226465, 20225619, 20226525, 20225923, 20227569, 20226243, 20227597, 20229581, 20227629,
#                   20227645,
#                   20227733, 20229367, 20227881, 20227901, 20229379, 20229387, 20227945, 20227925, 20227845, 20227887,
#                   20227911,
#                   20227957, 20228019, 20228057, 20228125, 20227977, 20228035, 20229445, 20228185, 20228221, 20228267,
#                   20228313,
#                   20228351, 20228647, 20228453, 20228413, 20228547, 20228535, 20228669, 20228707, 20228799, 20228915,
#                   948090642,
#                   20228885, 20228731, 20228415, 20228605, 20228559, 20228263, 20229417, 20229419, 20228311, 20228515,
#                   20229423,
#                   20229421, 20228365, 20229455, 20228697, 20229451, 20229447, 20227937, 20227897, 20227859, 20227829,
#                   20229381,
#                   20227819, 20227921, 20227779, 20227759, 20227739, 20227747, 20227725, 20229375, 20229373, 20227619,
#                   20229365,
#                   20227679, 20227757, 20226227, 20227681, 20226225, 20226223, 20226233, 20226235, 20226231, 20226239,
#                   20226529,
#                   20226017, 20226179, 20226051, 20226067, 20226047, 20226049, 20226045, 20226013, 20225963, 20225995,
#                   20225975,
#                   20225959, 20225901, 20225917, 20225897, 20225937, 20226155, 20226175, 20226153, 20226207, 20226219,
#                   20226545,
#                   20226541, 20226127, 20226109, 20226489, 20225773, 20225799, 20225817, 20225827, 20225843, 20225895,
#                   20225885,
#                   20226523, 20225881, 20225853, 20225847, 20225835, 20225823, 20225795, 20225767, 20225743, 20225723,
#                   20225733,
#                   20226481, 20225675, 20225699, 20225677, 20225693, 20225681, 20225679, 20226475, 20228543, 20228517,
#                   20228541,
#                   20228519, 20228377, 20228355, 20228353, 20228471, 20227851, 20227907, 20227783, 20227785, 20228011,
#                   20228003,
#                   20228005, 20228099, 20228227, 20228329, 20228385, 20228399, 20228531, 20228473, 20228833, 20228841,
#                   948090641,
#                   20228791, 20228859, 20229005, 20228947, 20228765, 20228417, 20228589, 20228579, 20228555, 20228513,
#                   20228309,
#                   20228247, 20228251, 20228369, 20229457, 20228743, 20228675, 20228673, 20228307, 20228081, 20228079,
#                   20228083,
#                   20227939, 20228045, 20228061, 20228069, 20228089, 20228063, 20228091, 20227879, 20227871, 20229573,
#                   20227777,
#                   20227707, 20229575, 20227753, 20227711, 20229377, 20227743, 20227709, 20227705, 20229371, 20227807,
#                   20227731,
#                   20229583, 20227605, 20227683, 20227603, 20227601, 20227559, 20229577, 20227557, 20227797, 20227727,
#                   20227669,
#                   20227561, 20227555, 20226547, 20226203, 20227565, 20227599, 20227567, 20227545, 20226609, 20227543,
#                   20227563,
#                   20226205, 20226007, 20226011, 20226531, 20225967, 20225983, 948090626, 948090627, 20226077, 20226043,
#                   20226191,
#                   20226533, 20226053, 20226063, 20226061, 20226055, 20225965, 20225961, 20225969, 20225949, 20225935,
#                   20225919,
#                   20226101, 20226095, 20226111, 20226105, 20226115, 948090250, 948090251, 948090252, 20226125, 20226119,
#                   20226113,
#                   20226129, 20226135, 20226137, 20226151, 20226543, 20225803, 20225851, 20225859, 20225739, 20225731,
#                   20226479,
#                   20225705, 20225695, 20226477, 948090344, 20228641, 948090379, 20228551, 20228553, 20228537, 20228549,
#                   20228469,
#                   20228375, 20228883, 20228905, 20228897, 20228763, 20228691, 20228761, 20228889, 20228805, 20228929,
#                   20228825,
#                   20228735, 20228813, 20228771, 20228737, 20228909, 20228895, 20228935, 20228499, 20229481, 20228727,
#                   20229471,
#                   20228371, 20228383, 20228511, 20228467, 20228281, 20229427, 20228637, 20228687, 20228701, 20228787,
#                   20228779,
#                   20228599, 20228569, 20228617, 20228625, 20228821, 20229475, 20229487, 20229485, 20229479, 948090652,
#                   20229453,
#                   20228287, 20229443, 20228127, 20228065, 20228041, 20228039, 20228189, 20228201, 20228925, 20228923,
#                   20229461,
#                   20228291, 20228581, 20226493, 20225779, 20224643, 20224419, 20228427, 948090460, 20229465, 20228545,
#                   20228611,
#                   20228705, 20228643, 20228689, 20228789, 20228757, 20228759, 20228811, 20228827, 20228845, 20228829,
#                   20228835,
#                   20228815, 20228773, 20228495, 20229469, 20228609, 20228931, 20228301, 20228315, 20228319, 20228327,
#                   20228305,
#                   20228343, 20228299, 20228317, 20228429, 20228441, 20228447, 20228613, 20228653, 20228667, 20228503,
#                   20228527,
#                   20228341, 20228507, 20229477, 20228685, 20228607, 948090653, 20228303, 20228261, 20228217, 20228215,
#                   20229431,
#                   20228119, 20228059, 20229429, 20228457, 20229463, 20228481, 20228497, 20228463, 20228509, 20225633,
#                   20228103,
#                   20228135, 20227625, 20229579, 948090253, 20226925, 20225951, 20226025, 20226027, 20226023, 20226099,
#                   20226147,
#                   20226163, 20226211, 20227823, 20227839, 20227847, 20227855, 20227861, 20227895, 20227909, 20227913,
#                   20227917,
#                   20227979, 20227985, 20227995, 20228013, 20228015, 20228047, 20228055, 20228113, 20228115, 948090635,
#                   948090636,
#                   20228155, 20228159, 20228177, 948090633, 20228199, 948090634, 20226917, 20226919, 20226921, 20224389,
#                   20223921,
#                   20225829, 20225889, 20225891, 20225819, 20225811, 20225777, 20225765, 20225713, 20225665, 20224403,
#                   20224373,
#                   20224371, 20224619, 20224253, 20223871, 948090614, 948090615, 948091085, 948090600, 948090601,
#                   948090602,
#                   948091086, 20225703, 948090381, 948090382, 20225687, 20225685, 20225697, 948090622, 948090623,
#                   20225953, 20223811,
#                   948090208, 948090209, 948090207, 20225001, 20224087, 20224055, 20223983, 20223935, 20223919, 20224053,
#                   20223985,
#                   20224013, 20224987, 20224069, 20224985, 20224063, 20224345, 20225663, 20225079, 20225099, 20225013,
#                   20225509,
#                   20225045, 20225507, 20225019, 20225063, 20225097, 20225519, 20225111, 20225021, 20225023, 20225027,
#                   20225081,
#                   20225093, 20225105, 20225103, 20225091, 20225527, 20225129, 20225143, 20225149, 20225145, 20225135,
#                   20225147,
#                   20225529, 20225151, 20225153, 20225155, 20225159, 20225861, 20225201, 20225165, 20225167, 20225171,
#                   20225175,
#                   20225181, 20225189, 20225199, 20225191, 20225941, 20225933, 20226527, 20225957, 20225981, 20225231,
#                   20225985,
#                   20225221, 20225211, 20225205, 20225207, 20225233, 20225235, 20225999, 20226019, 20226021, 948090625,
#                   20226085,
#                   20225237, 20225531, 20225251, 20225247, 20227549, 20226149, 20226215, 20227547, 20227551, 20226245,
#                   20227615,
#                   20226209, 20226829, 20227635, 20227657, 20227647, 20226875, 20227687, 20226873, 20226851, 20226837,
#                   20226835,
#                   20226853, 20226831, 20226833, 20226847, 20226839, 20226845, 20226869, 20226877, 20227775, 20226881,
#                   20226879,
#                   20226883, 20227769, 20227741, 20227801, 20227815, 20227695, 20227717, 20227703, 20227803, 20227791,
#                   20227765,
#                   20227811, 20227755, 20227767, 20227761, 20227763, 20227793, 20227813, 20227795, 20227773, 20227831,
#                   20227853,
#                   20227873, 20227863, 20227865, 20227981, 20227987, 20227991, 20227891, 20227893, 20227951, 20228049,
#                   20228121,
#                   20228123, 20228161, 20226911, 20226915, 20227487, 20226929, 20226933, 20226937, 20226939, 20228561,
#                   20228651,
#                   20228501, 20228603, 20228633, 20228679, 20228857, 20228893, 20228837, 20228871, 20228801, 20228725,
#                   20228741,
#                   20228659, 20228449, 20228597, 20228175, 20228209, 20229437, 20228111, 20227867, 20226885, 20227849,
#                   20226893,
#                   20227983, 20227903, 20226903, 20226901, 20228067, 20228051, 20228027, 20227971, 20227943, 20227933,
#                   948090598,
#                   20223897, 20223917, 948090210, 20223995, 20224019, 948090605, 948090606, 20225005, 20224081,
#                   948090432, 20224083,
#                   20224979, 20224993, 20224991, 20235769, 20224085, 20223869, 948090211, 20223893, 20223911, 948090603,
#                   948090604,
#                   948090407, 948090408, 20223981, 20224011, 20223989, 20224073, 20224091, 20224075, 20224089, 20224355,
#                   948091321,
#                   20224339, 20224343, 20224349, 20224337, 20224341, 948090394, 20225657, 20225653, 20225661, 20226473,
#                   20225047,
#                   20225041, 20224999, 20225007, 20225011, 20225501, 20225061, 20225059, 20225083, 20225029, 20225647,
#                   20225025,
#                   20225683, 948090190, 20225691, 20225073, 20225077, 20225085, 20225089, 20225087, 20225075, 20225701,
#                   20225815,
#                   20225793, 20225785, 20225133, 20225127, 20225131, 20225525, 20225137, 20225523, 20225141, 20225139,
#                   20225787,
#                   20225801, 20225845, 20225841, 20225161, 20225157, 20225839, 20225831, 20225833, 20225863, 20225865,
#                   20225871,
#                   20225185, 20225887, 20225197, 20225193, 20225867, 20225169, 20225873, 20225173, 20225179, 20225177,
#                   20225187,
#                   20225183, 20225195, 20225911, 948090269, 20225927, 20225929, 20225931, 20225939, 20225925, 20225913,
#                   20226001,
#                   20225993, 20225989, 20225987, 20225535, 20225229, 20225219, 20225223, 20225225, 20225213, 20225209,
#                   20225227,
#                   20225217, 20225215, 20225997, 20226005, 20226009, 948090624, 20226057, 20226071, 20225249, 20226059,
#                   20225245,
#                   20225241, 20225243, 20225239, 20226121, 20226143, 20226171, 20226189, 20226195, 20226257, 20226549,
#                   20226255,
#                   20226169, 20226199, 20226247, 20229369, 20227631, 20227653, 20227659, 20227667, 20227661, 20227637,
#                   20227641,
#                   20227643, 20227651, 20227649, 20227673, 20227685, 20227691, 20227689, 20227497, 20226859, 20226857,
#                   20227483,
#                   20226863, 20226855, 20226849, 20226865, 20226861, 20226841, 20226843, 20227693, 20227697, 20227721,
#                   20227491,
#                   20226867, 20235773, 20235771, 20226871, 20227805, 20227723, 20227719, 20227749, 20227737, 20227745,
#                   20227787,
#                   20227817, 20227715, 20227919, 20227875, 20227997, 20228017, 20227949, 20228147, 20228179, 20228151,
#                   20228153,
#                   20226923, 20226935, 20229441, 20228407, 20228405, 20228483, 20228433, 20228455, 20228533, 20228573,
#                   20228635,
#                   20228797, 20228807, 20228803, 20228809, 20228621, 20228393, 20228149, 20228107, 20228109, 20228007,
#                   20227869,
#                   20227857, 20228009, 20227989, 20227973, 20227905, 20227975, 20226905, 20227877, 20227969, 20228043,
#                   20227993,
#                   20228031, 20228071, 20228033, 20228023, 20227961, 20227935, 20226065, 20226083, 20226037, 20226485,
#                   20225669,
#                   20227885, 20227915, 20227955, 20227959, 20228021, 20228037, 20226177, 20226145, 20226097, 20225979,
#                   20225955,
#                   20225971, 20226087, 20226185, 20225973, 20225977, 20226003, 20225689, 20225671, 20226035, 20226141,
#                   20226075,
#                   20226069, 20226091, 20226117, 20225261, 20226197, 20225259, 20226167, 20226201, 20226183, 20228793,
#                   20228933,
#                   20228775, 20228903, 20228873, 20228907, 20228505, 20228293, 20228331, 20228337, 20228575, 20228437,
#                   20228465,
#                   20228525, 20228699, 20228747, 20228657, 20228619, 20228723, 20228695, 20228777, 20228831, 20228879,
#                   20228577,
#                   20228539, 20228487, 20228565, 20228713, 20223971, 20223961, 20223947, 20223991, 20223957, 20226897,
#                   20226887,
#                   20226889, 20226895, 20226931, 20228623, 20225775, 20225763, 20225781, 20225749, 20225109, 20225101,
#                   20225751,
#                   20225113, 20224631, 20224629, 20224399, 948090617, 20223859, 20224387, 20224639, 20225069, 20225065,
#                   20225049,
#                   20226941, 948090905, 948090906, 20226079, 20226107, 20226131, 20226123, 20226081, 20226073, 20225257,
#                   20226103,
#                   20226133, 20226161, 20226165, 20226173, 20226159, 20228711, 20228721, 20228781, 20228795, 20228843,
#                   20228851,
#                   20228855, 20228783, 20228817, 20228865, 20228863, 20228861, 20228849, 20228709, 20228345, 20228347,
#                   20228349,
#                   20228339, 20228373, 20228387, 20228391, 20228395, 20228431, 20228451, 20228397, 20228421, 20228439,
#                   20228523,
#                   20228521, 20228571, 20228587, 20228591, 20228601, 20228593, 20228629, 20228785, 20228489, 20223923,
#                   20223937,
#                   20224257, 20224255, 20226907, 948090472, 948090473, 948090474, 20226899, 20226891, 20228249, 20228269,
#                   20228321,
#                   20227493, 20228285, 20228379, 20227499, 20228461, 20225809, 20225735, 20225737, 20225729, 20225727,
#                   20225725,
#                   20225747, 20225761, 20224401, 20224395, 20224397, 948090616, 20224383, 20224369, 20224617, 20224385,
#                   20224407,
#                   20225637, 20225631, 20225667, 20225051, 20225053, 20225947, 20225875, 20227489, 20225017, 20229585,
#                   20228445,
#                   20224335, 20223821, 20225641, 20228381, 20229525, 20229523, 948090629, 20226553, 20226555, 20226557,
#                   20226559,
#                   20224645, 20224647, 948090618, 20224651, 20224653, 20224655, 948090903, 20224659, 20226591, 948091087,
#                   948091088,
#                   20226595, 20226597, 20226599, 20226601, 20226603, 20226605, 20226607, 20226561, 20226563, 20226565,
#                   20226567,
#                   20226569, 20226571, 20226573, 948090631, 20226577, 20226579, 20226581, 20226583, 20226585, 20226587,
#                   20226589,
#                   20224661, 20224663, 20224665, 948090630, 948090191, 948090192, 948090212, 948090213, 948090214,
#                   948090215,
#                   948090216, 948090256, 948090257, 948090258, 948090259, 948090345, 948090632, 948090383, 948090628,
#                   948090619,
#                   948090395, 948090461, 948090462, 948090902, 948090904, 948091047, 948091049, 948091048, 948091322,
#                   20223933,
#                   20223843, 20223829, 20223875, 20223831, 20223825, 20223839, 20223909, 20223863, 20223867, 20223877,
#                   20223915,
#                   20223913, 20223907, 20223967, 20223941, 20224061, 20224007, 20224997, 20224027, 20224243, 20223977,
#                   20224981,
#                   20224023, 20223945, 20223979, 20223951, 20224017, 20224057, 20224995, 20223823, 20223905, 20223931,
#                   20223827,
#                   20223841, 20223857, 20223873, 20223849, 20223833, 20223887, 20223889, 20223885, 20223883, 20223879,
#                   20224235,
#                   20223881, 20224237, 20223895, 20223903, 20223939, 20224239, 20224005, 20223993, 20224003, 20224009,
#                   20224021,
#                   20224033, 20224047, 20224051, 20224251, 20224049, 20224045, 20224035, 20224245, 20224037, 20224071,
#                   20224043,
#                   20224041, 20224015, 20223987, 20223949, 20224077, 20223865, 20223819, 20223837, 20223845, 20223855,
#                   20224231,
#                   20223891, 20223975, 20223929, 20223953, 20223997, 20224025, 20224029, 948090612, 20225037, 20225055,
#                   20225043,
#                   20225517, 20225513, 20225503, 20225505, 20225067, 20223817, 20223835, 948090599, 20223851, 20224229,
#                   20224233,
#                   20223927, 20223943, 20223969, 20224001, 948090613, 20225009, 20224247, 20225015, 20224079, 948090620,
#                   948090621,
#                   20224249, 20224983, 948090371, 20225031, 20225039, 948090337, 948090338, 948090339, 948090340,
#                   948090341, 20222667,
#                   20222595, 20222749, 20223351, 20223357, 20223007, 20223009, 20223021, 20223025, 20223791, 20223759,
#                   20223771,
#                   20223789, 20223695, 20223657, 20223679, 20223665, 20223549, 20223055, 20223101, 20223367, 20223559,
#                   20223565,
#                   20223561, 20223581, 20223573, 20222937, 20222965, 20222939, 20222921, 20222927, 20222899, 20222967,
#                   20222975,
#                   20222989, 20223027, 20222859, 20222731, 20223301, 20222733, 20223297, 20222745, 20222765, 20222785,
#                   20222793,
#                   20222833, 20222863, 20222843, 20222797, 20222777, 20223333, 20223331, 948090591, 948090592, 948090593,
#                   20223387,
#                   20222763, 20222759, 20222753, 20223319, 20222727, 20222725, 20222717, 20222713, 20222707, 20223291,
#                   20222739,
#                   20223309, 20223307, 20222697, 20222673, 20222651, 20222633, 20222625, 20223775, 20223777, 20223139,
#                   20223661,
#                   20223663, 20223031, 20223083, 20223105, 20223111, 20223135, 20223361, 20223123, 20224199, 20223129,
#                   20223551,
#                   20223131, 20223133, 20222987, 20222949, 20222947, 20222953, 20222951, 20222919, 20222897, 20222973,
#                   20222977,
#                   20222979, 20222935, 20222861, 20222815, 20222795, 20223339, 20222743, 20222741, 20222737, 20223299,
#                   20222789,
#                   20222867, 948090370, 20222841, 20222875, 20223345, 20222799, 20223091, 948090326, 948090589, 20222641,
#                   20222709,
#                   20222643, 20223315, 20223313, 20223311, 20223327, 20222665, 20222671, 20222627, 20222635, 20222653,
#                   20223303,
#                   20222755, 20222701, 20222683, 20222689, 20222685, 20222719, 20222729, 948090590, 20223317, 20222711,
#                   20222769,
#                   20223305, 20223293, 20223321, 20222705, 20222715, 20222691, 20223347, 20223379, 20223329, 20222779,
#                   20223383,
#                   20223385, 20222877, 20223381, 948090221, 948090222, 948090223, 948090224, 948090225, 948090226,
#                   948090227,
#                   948090228, 948090229, 948090463, 948090464, 20223287, 20223081, 20223667, 948091081, 20223699,
#                   20224613, 20223797,
#                   20223783, 20223793, 20223801, 20223803, 20223795, 20223753, 20224209, 20223719, 20223723, 20223755,
#                   20223773,
#                   20223769, 20223711, 20223701, 20223731, 20223727, 20223685, 20224307, 20224305, 20223687, 20223747,
#                   20223751,
#                   20223677, 20223613, 20223615, 20223637, 20223597, 20223605, 20223595, 20223627, 20223629, 20223585,
#                   20223583,
#                   20223599, 20223625, 20223669, 20223655, 20223633, 20223563, 20223567, 20223571, 20223075, 20223121,
#                   20223547,
#                   20223119, 20223125, 20223067, 20223113, 20223363, 20223077, 20223109, 20223095, 20223051, 20222925,
#                   20222991,
#                   20222923, 20223359, 20223043, 20223017, 20223035, 20222955, 20222915, 20222883, 20222879, 20222835,
#                   20222819,
#                   20222981, 20222995, 20222997, 20223001, 20222983, 20223049, 20222943, 20222871, 20222901, 20222887,
#                   20222959,
#                   20223353, 20222805, 20222791, 20222783, 20222831, 20222695, 20222679, 20222677, 20222663, 20223289,
#                   20222659,
#                   20222649, 20222647, 20223283, 20223713, 20223649, 948090596, 948090597, 20223589, 948090607,
#                   948090608, 20223555,
#                   948090594, 948090595, 948090204, 948090609, 948090610, 948090363, 948090611, 20223799, 20224221,
#                   20223781,
#                   20223785, 20224225, 20223739, 20224211, 20223757, 20223763, 20223765, 20223741, 20223743, 20223729,
#                   20223715,
#                   20224215, 948090206, 20223749, 20223745, 20223725, 20223721, 20223703, 20223707, 20223709, 20223705,
#                   20223653,
#                   948091042, 20223675, 948090200, 20223639, 20223603, 20223647, 948090202, 20224207, 20223557, 20223593,
#                   20223641,
#                   20223659, 20223631, 20223645, 20223651, 20224205, 20223569, 20223143, 20223577, 948090369, 20223117,
#                   20223087,
#                   20223115, 20223365, 20223085, 20223145, 20223079, 20223073, 20223127, 948090217, 20223103, 20223063,
#                   20223059,
#                   20223069, 20223065, 20223071, 20223053, 20222993, 20223039, 948090469, 20223033, 20223019, 20235767,
#                   20223037,
#                   20222931, 20222913, 20222825, 20223047, 20223041, 20223013, 20223011, 20222999, 20222893, 20222873,
#                   20222885,
#                   20222929, 20222865, 20222839, 20222829, 20223335, 20223337, 20222781, 20222801, 20223341, 20222837,
#                   20222851,
#                   20222857, 20222845, 20223343, 20223323, 20222757, 20222735, 20223325, 20222723, 20223295, 20222703,
#                   20222721,
#                   20222675, 20222645, 20223285, 20222661, 20223281, 20222669, 20222699, 20222681, 20223689, 20223693,
#                   20224611,
#                   20224311, 20222773, 948091083, 948091084, 20222775, 20222817, 948091080, 20223369, 20223371, 20223373,
#                   20223375,
#                   20223377, 948090199, 948090201, 948090203, 948090923, 948090924, 948090364, 948091082, 948091043,
#                   948091044,
#                   948091046, 948091045]
#     reservoir_comid_list = [120051930, 1214501, 10814778, 14596315, 10816386, 4876219, 3906255, 4875263, 4876263, 4899751, 10375440, 10091800, 10408798, 10329965, 5302091, 1200014, 3501837, 11975087, 11965847, 11979229, 1392281, 10276260, 10091588, 10273702]
#
#     start_subset(job_id=job_id, netcdf_folder_path=netcdf_folder_path, output_folder_path=output_folder_path,
#                  template_folder_path=template_folder_path, simulation_date_list=simulation_date_list,
#                  data_type_list=data_type_list, model_type_list=model_type_list, file_type_list=file_type_list,
#                  grid_dict=grid_dict, stream_comid_list=stream_comid_list, reservoir_comid_list=reservoir_comid_list,
#                  merge_netcdfs=merge_netcdfs, cleanup=cleanup, write_file_list=write_file_list)
