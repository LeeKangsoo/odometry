import argparse
import os

import __init_path__
import env

from slam.preprocessing import DatasetPreparator, get_default_dataset_parser


if __name__ == '__main__':
    parser = get_default_dataset_parser()
    parser.add_argument('--dataset_root', type=str,
                        default=os.path.join(env.DATASET_PATH, 'KITTI_odometry_2012/dataset/sequences/'))
    args = parser.parse_args()
    width = 320
    height = 96

    DatasetPreparator(dataset_type='KITTI',
                      dataset_root=args.dataset_root,
                      output_root=args.output_dir,
                      target_size=(height, width),
                      optical_flow_checkpoint=args.of_checkpoint,
                      stride=args.stride,
                      depth_checkpoint=args.depth_checkpoint if args.depth else None,
                      binocular_depth_checkpoint=args.binocular_depth_checkpoint if args.binocular_depth else None,
                      indices_root=args.indices_root).prepare()
