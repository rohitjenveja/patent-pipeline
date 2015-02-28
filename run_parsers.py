#!/usr/bin/python

"""Job to look sqs and decide what parsers to run."""

from parsers import us_patent


PARSER_MAP = {'us': us_patent.USPatent}


def GrabFromQueue():
  # use amazon sqs to gather which s3 us patents need to be processed
  s3_location = './sample_data/US08671673-20140318.XML'
  yield 'us', s3_location


def main():
  # Empty out any items left in SQS.
  for type, item in GrabFromQueue():
    parser = PARSER_MAP[type](item)
    #return_code = parser.process()
    #if return_code: 
    #  # moves to a complete folder.
    #  # removes from sqs
    # else
    #  parser.mark_success()
    #  # remove from sqs?
    #  # log some sort of error.


if __name__ == "__main__":
  main()
