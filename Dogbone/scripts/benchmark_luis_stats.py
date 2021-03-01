import csv


passed = 0
total = 0
deviation_sum = 0.
pos_but_no_subject = []
pos_but_no_subject_text = []
positives = []
negatives = []

with open('jurisdiction_benchmark.csv', 'r') as csvin:
    csvreader = csv.reader(csvin, delimiter=',',
                            quotechar='"')
    csvreader.next()
    for row in csvreader:
        fname, hglt, nmc, orig_score, text, label, score, subject, predicted  = row

        total += 1

        if predicted == label:
            passed += 1

        if int(label) == 1:
            if not subject:
                pos_but_no_subject.append(float(score))
                pos_but_no_subject_text.append(text)

        if int(predicted) == 1:
            positives.append(float(score))
            deviation_sum += 1. - float(score)
        else:
            negatives.append(float(score))
            deviation_sum += float(score)

print 'Accuracy: %.2f%%  (%d/%d)' % (100 * passed / float(total or 0.00001), passed, total)
print 'Mean Deviation: %.3f' % (deviation_sum / float(total or 0.00001))

print 'Subject Accuracy: %.2f%%  (%d/%d)' % (100 * len(pos_but_no_subject) / float(len(positives) or 0.00001), len(pos_but_no_subject), len(positives))
print 'Mean Score NO_SUBJ: %.3f' % (sum(pos_but_no_subject) / len(pos_but_no_subject))

# print ' ---- '*30
# print '\n\n'.join(pos_but_no_subject_text)
# print ' ---- '*30


import pylab as plt

plt.hist(positives, facecolor='green', alpha=0.5, bins=25)
plt.hist(negatives, facecolor='red', alpha=0.5, bins=25)
plt.axvline(0.5, color='k', linestyle='--')
plt.title("Positives / Negatives distribution")
plt.xlabel("Score")
plt.ylabel("Frequency")
plt.savefig('pos-neg_distr.png')

