from argparse import ArgumentParser
import os
import shutil
import matplotlib.pyplot as plt
import torch
import numpy as np
from pathlib import Path

from xaivision.utils import (
    load_sample,
    load_models,
    check_model_data_compatibility,
    model_details,
    sample_details,
    check_onnx_torch_out,
    conv2d_feature_vis_extra_layers,
    conv2d_feature_vis_no_extra_layers,
    find_components,
)

from xaivision.xai_tools import (vision_shap,
                                 integrated_grad,
                                 deeplift,
                                 shap_overview,
                                 overall_score)

if __name__ == "__main__":

    parser = ArgumentParser(add_help=False)
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")

    optional.add_argument(
        "-d",
        "--dataset",
        type=str,
        default="data1.h5",
        help=("Select the dataset you want to examine "
                "which is placed in the /data folder"
              ),
    )

    optional.add_argument(
        "-m",
        "--model",
        type=str,
        default="model.onnx",
        help=("Select the model you want to use which "
              "is placed on /model folder"),
    )

    optional.add_argument(
        "-s",
        "--sample",
        type=int,
        default=8,
        help="Select the sample you want to examine",
    )
    optional.add_argument("-h",
                          "--help",
                          action="help",
                          help="show this help message and exit")

    args = parser.parse_args()

    if torch.backends.mps.is_available():
        mps_device = torch.device("mps")
    else:
        print("MPS device not found.")

    root_dir = str(Path(__file__).resolve().parent.parent)

    data_dir = os.path.join(root_dir, "data")

    model_dir = os.path.join(root_dir, "model")

    print("--------------------- Tango -------------------")
    print("Author")
    print("Squaredev")
    print("-------------------------------------------------------")

    for i, arg in enumerate(vars(args)):
        print("{}.{}: {}".format(i, arg, vars(args)[arg]))
        print("-------------------------------------------------------\n")

    folder_path = os.path.join(root_dir, "reports")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    model_path = os.path.join(model_dir, args.model)
    torch_model = load_models(model_path)

    data_path = os.path.join(data_dir, args.dataset)

    print("----FUNCTIONALITY 1----")

    # Functionality N1
    # Load model and dataset and checks if the output size of the
    # model corresponds to the exprected size of
    # the ground truth of the dataset
    model_input, ground_truth = load_sample(data_path, args.sample)

    if not check_model_data_compatibility(torch_model, model_input.shape,
                                          ground_truth.shape):
        raise ValueError("Data dont corespond to model's architecture")

    print("----FUNCTIONALITY 2----")

    # Functionality N2
    # Return the summary of the model
    # which includes layers, parameters and structure
    # and is stored as an image
    dot, sum = model_details(torch_model, model_input.shape)
    dot.render(folder_path + "/TorchModel_torchviz", format="png")
    print(sum)

    folder_path_sample = os.path.join(folder_path, "sample" + str(args.sample))
    path = Path(folder_path_sample)
    path.mkdir(parents=True, exist_ok=True)

    print("----FUNCTIONALITY 3----")

    # Functionality N3
    # We examine a specific datapoint
    # the sample details are stored as an image
    model_output = sample_details(torch_model, model_input)

    arr = model_input.copy()
    while 1 in arr.shape:
        arr = np.squeeze(arr)

    plt.imshow(arr)
    title = "Model_output: " + str(model_output) + "\n"
    title = title + "Ground Truth: " + str(ground_truth)
    plt.title(title)
    plt.savefig(folder_path_sample + "/sample.png")
    plt.close()

    print("----FUNCTIONALITY 4----")

    # Functionality N4
    # We convert the onnx to pytorch format
    # and check if we have the same output
    diagnosis = check_onnx_torch_out(model_path, torch_model, model_input)
    print(diagnosis)

    print("----FUNCTIONALITY 5----")

    # Functionality N5
    # Save features from conv2d layers extracted from the model
    # with only conv2d layers
    arrays, names = conv2d_feature_vis_no_extra_layers(torch_model,
                                                       model_input)

    num_arrays = len(arrays)
    num_rows = (num_arrays + 1) // 2  # Calculate the number of rows needed
    fig, axes = plt.subplots(num_rows, 2, figsize=(10, 5 * num_rows))
    fig.tight_layout(pad=3.0)
    for i, array in enumerate(arrays):
        row = i // 2
        col = i % 2
        ax = axes[row, col] if num_rows > 1 else axes[col]
        im = ax.imshow(array, cmap="viridis")
        plt.colorbar(im, ax=ax)
        ax.set_title(names[i].split("(")[0] + str(i))
    plt.savefig(folder_path_sample +
                "/activation_map_with_no_extra_layers.png")

    print("----FUNCTIONALITY 6----")

    # Functionality N6
    # Save features from conv2d layers extracted from the model
    arrays, names = conv2d_feature_vis_extra_layers(torch_model, model_input)

    num_arrays = len(arrays)
    num_rows = (num_arrays + 1) // 2  # Calculate the number of rows needed
    fig, axes = plt.subplots(num_rows, 2, figsize=(10, 5 * num_rows))
    fig.tight_layout(pad=3.0)
    for i, array in enumerate(arrays):
        row = i // 2
        col = i % 2
        ax = axes[row, col] if num_rows > 1 else axes[col]
        im = ax.imshow(array, cmap="viridis")
        plt.colorbar(im, ax=ax)
        ax.set_title(names[i].split("(")[0] + str(i))
    plt.savefig(folder_path_sample + "/activation_map_with_extra_layers.png")
    plt.close()

    print("----FUNCTIONALITY 7----")

    # Functionality N7
    # Save independent components from a single datapoint

    folder_path_components = os.path.join(folder_path_sample, "components")
    if os.path.exists(folder_path_components) and os.path.isdir(
            folder_path_components):
        shutil.rmtree(folder_path_components)

    path = Path(folder_path_components)
    path.mkdir(parents=True)
    components = 2

    heatmaps = find_components(torch_model, model_input, components)

    for i in range(components):
        plt.clf()
        plt.imshow(heatmaps[0][i])
        plt.savefig(folder_path_components + "/component_" + str(i + 1) +
                    ".png")
    plt.close()

    print("----FUNCTIONALITY 8----")

    # Functionality N8
    # Save shap overview results

    background = 100
    samples = 10

    overview_plt = shap_overview(data_path, background, samples, torch_model)

    for i, plot in enumerate(overview_plt):
        plot.savefig(folder_path + "/shap_overview_value_" + str(i) + ".png")
        plt.close()

    print("----FUNCTIONALITY 9----")

    # Functionality N9
    # Save vision shap results

    shap_plots, shap_table = vision_shap(data_path, background, torch_model,
                                         model_input)

    for i, plot in enumerate(shap_plots):
        plot.savefig(folder_path_sample + "/shap_value_" + str(i) + ".png")
        plt.close()

    arr = shap_table[0].copy()
    while 1 in arr.shape:
        arr = np.squeeze(arr)

    print("----FUNCTIONALITY 10----")

    # Functionality N10
    # Returns the overall score on a dataset

    check_samples = -1
    pixels, effect = overall_score(data_path, background, torch_model,
                                   check_samples)
    print("===============================================\
===========================================")
    print("Overall Score")
    print("Avg number of Pixels per expected output that dont belong to the \
          original image and have an effect for each target: ", pixels)
    print("Mean Effect of this pixels(lower == better): ", effect)

    print("----FUNCTIONALITY 11----")

    # Functionality N11
    # Save integrated gradient results
    grads = integrated_grad(torch_model, model_input)

    for i, array in enumerate(grads):
        plt.imshow(array)
        plt.savefig(folder_path_sample + "/integrated_grad_value_" +
                    str(i + 1) + ".png")
        plt.close()

    print("----FUNCTIONALITY 12----")

    # Functionality N12
    # Save deeplift results
    dl_plots = deeplift(torch_model, model_input)

    for i, array in enumerate(dl_plots):
        plt.imshow(array)
        plt.savefig(folder_path_sample + "/deep_lift_value_" + str(i + 1) +
                    ".png")
        plt.close()
